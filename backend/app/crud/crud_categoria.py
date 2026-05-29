from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Categoria


def get_categorias(db: Session, user_id: int) -> List[Categoria]:
    return db.query(Categoria).filter(
        Categoria.user_id.is_(None) | (Categoria.user_id == user_id)
    ).all()


def get_categoria(db: Session, categoria_id: int, user_id: int) -> Optional[Categoria]:
    return db.query(Categoria).filter(
        Categoria.id == categoria_id,
        (Categoria.user_id == user_id) | Categoria.user_id.is_(None),
    ).first()
