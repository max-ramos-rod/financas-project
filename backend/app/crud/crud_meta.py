from typing import Optional

from sqlalchemy.orm import Session

from app.models import Meta


def get_metas(db: Session, user_id: int) -> list[Meta]:
    return db.query(Meta).filter(Meta.user_id == user_id).all()


def get_meta(db: Session, meta_id: int, user_id: int) -> Optional[Meta]:
    return db.query(Meta).filter(Meta.id == meta_id, Meta.user_id == user_id).first()
