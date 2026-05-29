from typing import Optional

from sqlalchemy.orm import Session

from app.models import Meta
from app.schemas.meta import MetaCreate, MetaUpdate


def get_metas(db: Session, user_id: int) -> list[Meta]:
    return db.query(Meta).filter(Meta.user_id == user_id).all()


def get_meta(db: Session, meta_id: int, user_id: int) -> Optional[Meta]:
    return db.query(Meta).filter(Meta.id == meta_id, Meta.user_id == user_id).first()


def criar_meta(db: Session, meta: MetaCreate, user_id: int) -> Meta:
    db_meta = Meta(user_id=user_id, **meta.model_dump())
    db.add(db_meta)
    db.commit()
    db.refresh(db_meta)
    return db_meta


def atualizar_meta(db: Session, meta_id: int, user_id: int, meta_update: MetaUpdate) -> Optional[Meta]:
    db_meta = get_meta(db, meta_id, user_id)
    if not db_meta:
        return None
    for key, value in meta_update.model_dump(exclude_unset=True).items():
        setattr(db_meta, key, value)
    db.add(db_meta)
    db.commit()
    db.refresh(db_meta)
    return db_meta


def deletar_meta(db: Session, meta_id: int, user_id: int) -> bool:
    db_meta = get_meta(db, meta_id, user_id)
    if not db_meta:
        return False
    db.delete(db_meta)
    db.commit()
    return True
