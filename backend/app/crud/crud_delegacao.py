from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models import Delegacao, DelegacaoStatus, User


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
    return (
        db.query(Delegacao)
        .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
        .filter(Delegacao.id == delegacao_id)
        .first()
    )


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
    return (
        db.query(Delegacao)
        .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
        .filter(Delegacao.invite_token == token)
        .first()
    )


def is_invite_expired(delegacao: Delegacao) -> bool:
    if delegacao.invite_expires_at is None:
        return True
    return delegacao.invite_expires_at < datetime.now(timezone.utc)


def list_delegacoes_sent(db: Session, owner_user_id: int) -> List[Delegacao]:
    return (
        db.query(Delegacao)
        .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
        .filter(Delegacao.owner_user_id == owner_user_id)
        .order_by(Delegacao.created_at.desc())
        .all()
    )


def list_delegacoes_received(db: Session, delegate_user_id: int) -> List[Delegacao]:
    return (
        db.query(Delegacao)
        .options(joinedload(Delegacao.owner), joinedload(Delegacao.delegate))
        .filter(Delegacao.delegate_user_id == delegate_user_id)
        .order_by(Delegacao.created_at.desc())
        .all()
    )
