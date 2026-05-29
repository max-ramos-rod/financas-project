import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.contracts.delegacao import DelegacaoRepositoryProtocol
from app.crud.crud_user import create_user, get_user_by_email
from app.models import Delegacao, DelegacaoStatus, User, UserRole
from app.repositories.delegacao import DelegacaoRepository
from app.schemas.delegacao import DelegacaoConfirmRequest

INVITE_TTL_DAYS = 7


class DelegacaoService:
    def __init__(self, repo: DelegacaoRepositoryProtocol | None = None) -> None:
        self._repo: DelegacaoRepositoryProtocol = repo if repo is not None else DelegacaoRepository()

    @staticmethod
    def is_invite_expired(delegacao: Delegacao) -> bool:
        if delegacao.invite_expires_at is None:
            return True
        return delegacao.invite_expires_at < datetime.now(timezone.utc)

    def listar_enviadas(self, db: Session, owner_user_id: int) -> List[Delegacao]:
        return (
            db.query(Delegacao)
            .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
            .filter(Delegacao.owner_user_id == owner_user_id)
            .order_by(Delegacao.created_at.desc())
            .all()
        )

    def listar_recebidas(self, db: Session, delegate_user_id: int) -> List[Delegacao]:
        return (
            db.query(Delegacao)
            .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
            .filter(Delegacao.delegate_user_id == delegate_user_id)
            .order_by(Delegacao.created_at.desc())
            .all()
        )

    def buscar_por_id(self, db: Session, delegacao_id: int) -> Optional[Delegacao]:
        return (
            db.query(Delegacao)
            .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
            .filter(Delegacao.id == delegacao_id)
            .first()
        )

    def buscar_por_token(self, db: Session, token: str) -> Optional[Delegacao]:
        return (
            db.query(Delegacao)
            .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
            .filter(Delegacao.invite_token == token)
            .first()
        )

    def invite(
        self, db: Session, owner_user_id: int, invited_email: str, can_write: bool
    ) -> tuple[Delegacao, bool]:
        normalized_email = invited_email.strip().lower()
        invited_user: Optional[User] = (
            db.query(User).filter(User.email == normalized_email).first()
        )
        existing: Optional[Delegacao] = (
            db.query(Delegacao)
            .filter(Delegacao.owner_user_id == owner_user_id, Delegacao.invited_email == normalized_email)
            .first()
        )

        if existing and existing.status == DelegacaoStatus.ACTIVE:
            raise ValueError("Ja existe uma delegacao ativa para este e-mail.")

        invite_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)

        if existing:
            existing.delegate_user_id = invited_user.id if invited_user else None
            existing.status = DelegacaoStatus.PENDING
            existing.can_write = can_write
            existing.invited_email = normalized_email
            existing.invite_token = invite_token
            existing.invite_expires_at = expires_at
            existing.accepted_at = None
            existing.revoked_at = None
            self._repo._save(db, existing)
            db.commit()
            db.refresh(existing)
            return existing, invited_user is not None

        delegacao = Delegacao(
            owner_user_id=owner_user_id,
            delegate_user_id=invited_user.id if invited_user else None,
            invited_email=normalized_email,
            invite_token=invite_token,
            invite_expires_at=expires_at,
            status=DelegacaoStatus.PENDING,
            can_write=can_write,
        )
        self._repo._save(db, delegacao)
        db.commit()
        db.refresh(delegacao)
        return delegacao, invited_user is not None

    def accept(self, db: Session, delegacao: Delegacao) -> Delegacao:
        if delegacao.status != DelegacaoStatus.PENDING:
            raise ValueError("Apenas convites pendentes podem ser aceitos.")
        if self.is_invite_expired(delegacao):
            raise ValueError("Convite expirado.")
        if not delegacao.delegate_user_id:
            raise ValueError("Convite sem usuario associado.")

        delegacao.status = DelegacaoStatus.ACTIVE
        delegacao.accepted_at = datetime.now(timezone.utc)
        delegacao.revoked_at = None
        delegacao.invite_token = None
        delegacao.invite_expires_at = None
        self._repo._save(db, delegacao)
        db.commit()
        db.refresh(delegacao)
        return delegacao

    def revoke(self, db: Session, delegacao: Delegacao) -> Delegacao:
        delegacao.status = DelegacaoStatus.REVOKED
        delegacao.revoked_at = datetime.now(timezone.utc)
        delegacao.invite_token = None
        delegacao.invite_expires_at = None
        self._repo._save(db, delegacao)
        db.commit()
        db.refresh(delegacao)
        return delegacao

    def confirm(
        self, db: Session, delegacao: Delegacao, payload: DelegacaoConfirmRequest
    ) -> Delegacao:
        if not delegacao.delegate_user_id:
            existing_user = get_user_by_email(db, delegacao.invited_email)
            if existing_user:
                delegacao.delegate_user_id = existing_user.id
                db.add(delegacao)
                db.commit()
                db.refresh(delegacao)
            else:
                if not payload.nome or not payload.password:
                    raise ValueError("Nome e senha sao obrigatorios para concluir o cadastro")
                new_user = create_user(
                    db=db,
                    email=delegacao.invited_email,
                    password=payload.password,
                    nome=payload.nome,
                    role=UserRole.USER,
                )
                delegacao.delegate_user_id = new_user.id
                db.add(delegacao)
                db.commit()
                db.refresh(delegacao)

        return self.accept(db, delegacao)
