from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional

from app.models import Meta
from app.schemas.meta import MetaCreate, MetaUpdate


def get_metas(db: Session, user_id: int) -> List[Meta]:
    """Lista todas as metas do usuário"""
    return db.query(Meta).filter(Meta.user_id == user_id).all()


def get_meta(db: Session, meta_id: int, user_id: int) -> Optional[Meta]:
    """Busca uma meta específica"""
    return db.query(Meta).filter(
        and_(
            Meta.id == meta_id,
            Meta.user_id == user_id
        )
    ).first()


def criar_meta(db: Session, meta: MetaCreate, user_id: int) -> Meta:
    """Cria uma nova meta"""
    db_meta = Meta(
        user_id=user_id,
        **meta.model_dump()
    )
    db.add(db_meta)
    db.commit()
    db.refresh(db_meta)
    return db_meta


def atualizar_meta(db: Session, meta_id: int, user_id: int, meta_update: MetaUpdate) -> Optional[Meta]:
    """Atualiza uma meta existente"""
    db_meta = get_meta(db, meta_id, user_id)
    if not db_meta:
        return None
    
    # Atualiza apenas os campos fornecidos
    update_data = meta_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_meta, key, value)
    
    db.add(db_meta)
    db.commit()
    db.refresh(db_meta)
    return db_meta


def deletar_meta(db: Session, meta_id: int, user_id: int) -> bool:
    """Deleta uma meta"""
    db_meta = get_meta(db, meta_id, user_id)
    if not db_meta:
        return False
    
    db.delete(db_meta)
    db.commit()
    return True
