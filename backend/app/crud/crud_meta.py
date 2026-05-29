from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Meta
from app.schemas.meta import MetaCreate, MetaUpdate


class CRUDMeta(CRUDBase[Meta, MetaCreate, MetaUpdate]):
    def get_metas(self, db: Session, user_id: int):
        return self.get_multi(db, user_id)

    def get_meta(self, db: Session, meta_id: int, user_id: int):
        return self.get(db, meta_id, user_id)

    def criar_meta(self, db: Session, meta: MetaCreate, user_id: int) -> Meta:
        return self.create(db, meta, user_id)

    def atualizar_meta(self, db: Session, meta_id: int, user_id: int, meta_update: MetaUpdate):
        db_meta = self.get(db, meta_id, user_id)
        if not db_meta:
            return None
        return self.update(db, db_meta, meta_update)

    def deletar_meta(self, db: Session, meta_id: int, user_id: int) -> bool:
        return self.remove(db, meta_id, user_id)


crud_meta = CRUDMeta(Meta)

# Module-level aliases preserve the existing `crud.get_metas(db, user_id)` call style
get_metas = crud_meta.get_metas
get_meta = crud_meta.get_meta
criar_meta = crud_meta.criar_meta
atualizar_meta = crud_meta.atualizar_meta
deletar_meta = crud_meta.deletar_meta
