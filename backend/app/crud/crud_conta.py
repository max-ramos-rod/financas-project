from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Conta


def get_contas(db: Session, user_id: int) -> List[Conta]:
    return db.query(Conta).filter(Conta.user_id == user_id).all()


def get_conta(db: Session, conta_id: int, user_id: int) -> Optional[Conta]:
    return db.query(Conta).filter(
        and_(Conta.id == conta_id, Conta.user_id == user_id)
    ).first()
