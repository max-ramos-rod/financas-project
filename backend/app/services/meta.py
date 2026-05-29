from typing import Optional

from sqlalchemy.orm import Session

from app.contracts.meta import MetaRepositoryProtocol
from app.models import Meta
from app.repositories.meta import MetaRepository
from app.schemas.meta import MetaCreate, MetaUpdate


class MetaService:
    def __init__(self, repo: MetaRepositoryProtocol | None = None) -> None:
        self._repo: MetaRepositoryProtocol = repo if repo is not None else MetaRepository()

    def criar(self, db: Session, meta: MetaCreate, user_id: int) -> Meta:
        db_meta = Meta(user_id=user_id, **meta.model_dump())
        self._repo._save(db, db_meta)
        db.commit()
        db.refresh(db_meta)
        return db_meta

    def atualizar(
        self, db: Session, meta_id: int, user_id: int, meta_update: MetaUpdate
    ) -> Optional[Meta]:
        db_meta = db.query(Meta).filter(Meta.id == meta_id, Meta.user_id == user_id).first()
        if not db_meta:
            return None
        for key, value in meta_update.model_dump(exclude_unset=True).items():
            setattr(db_meta, key, value)
        self._repo._save(db, db_meta)
        db.commit()
        db.refresh(db_meta)
        return db_meta

    def deletar(self, db: Session, meta_id: int, user_id: int) -> bool:
        db_meta = db.query(Meta).filter(Meta.id == meta_id, Meta.user_id == user_id).first()
        if not db_meta:
            return False
        self._repo.delete(db, db_meta)
        db.commit()
        return True
