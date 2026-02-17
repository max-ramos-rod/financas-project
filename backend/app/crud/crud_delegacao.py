import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models import Delegacao, DelegacaoStatus, User

INVITE_TTL_DAYS = 7


def get_active_delegacao(
    db: Session,
    owner_user_id: int,
    delegate_user_id: int,
) -> Optional[Delegacao]:
    return db.query(Delegacao).filter(
        and_(
            Delegacao.owner_user_id == owner_user_id,
            Delegacao.delegate_user_id == delegate_user_id,
            Delegacao.status == DelegacaoStatus.ACTIVE,
        )
    ).first()


def get_delegacao_by_id(db: Session, delegacao_id: int) -> Optional[Delegacao]:
    return db.query(Delegacao).options(
        joinedload(Delegacao.owner),
        joinedload(Delegacao.delegate),
    ).filter(Delegacao.id == delegacao_id).first()


def get_delegacao_owner_delegate(
    db: Session,
    owner_user_id: int,
    delegate_user_id: int,
) -> Optional[Delegacao]:
    return db.query(Delegacao).filter(
        and_(
            Delegacao.owner_user_id == owner_user_id,
            Delegacao.delegate_user_id == delegate_user_id,
        )
    ).first()


def get_delegacao_owner_email(
    db: Session,
    owner_user_id: int,
    invited_email: str,
) -> Optional[Delegacao]:
    normalized_email = invited_email.strip().lower()
    return db.query(Delegacao).filter(
        and_(
            Delegacao.owner_user_id == owner_user_id,
            Delegacao.invited_email == normalized_email,
        )
    ).first()


def get_delegacao_by_token(db: Session, token: str) -> Optional[Delegacao]:
    return db.query(Delegacao).options(
        joinedload(Delegacao.owner),
        joinedload(Delegacao.delegate),
    ).filter(Delegacao.invite_token == token).first()


def is_invite_expired(delegacao: Delegacao) -> bool:
    if delegacao.invite_expires_at is None:
        return True
    return delegacao.invite_expires_at < datetime.now(timezone.utc)


def invite_delegacao(
    db: Session,
    owner_user_id: int,
    invited_email: str,
    can_write: bool,
) -> tuple[Delegacao, bool]:
    normalized_email = invited_email.strip().lower()
    invited_user = db.query(User).filter(User.email == normalized_email).first()
    existing = get_delegacao_owner_email(db, owner_user_id, normalized_email)

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
        db.add(existing)
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
    db.add(delegacao)
    db.commit()
    db.refresh(delegacao)
    return delegacao, invited_user is not None


def list_delegacoes_sent(db: Session, owner_user_id: int) -> List[Delegacao]:
    return db.query(Delegacao).options(
        joinedload(Delegacao.owner),
        joinedload(Delegacao.delegate),
    ).filter(Delegacao.owner_user_id == owner_user_id).order_by(Delegacao.created_at.desc()).all()


def list_delegacoes_received(db: Session, delegate_user_id: int) -> List[Delegacao]:
    return db.query(Delegacao).options(
        joinedload(Delegacao.owner),
        joinedload(Delegacao.delegate),
    ).filter(Delegacao.delegate_user_id == delegate_user_id).order_by(Delegacao.created_at.desc()).all()


def accept_delegacao(db: Session, delegacao: Delegacao) -> Delegacao:
    if delegacao.status != DelegacaoStatus.PENDING:
        raise ValueError("Apenas convites pendentes podem ser aceitos.")
    if is_invite_expired(delegacao):
        raise ValueError("Convite expirado.")
    if not delegacao.delegate_user_id:
        raise ValueError("Convite sem usuario associado.")

    delegacao.status = DelegacaoStatus.ACTIVE
    delegacao.accepted_at = datetime.now(timezone.utc)
    delegacao.revoked_at = None
    delegacao.invite_token = None
    delegacao.invite_expires_at = None
    db.add(delegacao)
    db.commit()
    db.refresh(delegacao)
    return delegacao


def revoke_delegacao(db: Session, delegacao: Delegacao) -> Delegacao:
    delegacao.status = DelegacaoStatus.REVOKED
    delegacao.revoked_at = datetime.now(timezone.utc)
    delegacao.invite_token = None
    delegacao.invite_expires_at = None
    db.add(delegacao)
    db.commit()
    db.refresh(delegacao)
    return delegacao
