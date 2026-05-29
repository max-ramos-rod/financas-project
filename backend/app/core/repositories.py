from __future__ import annotations

from abc import ABC
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams

ModelT = TypeVar("ModelT")
EntityT = TypeVar("EntityT")


class SQLAlchemyRepository(Generic[ModelT], ABC):
    model: type[ModelT]

    def list(self, db: Session, *, order_by: Any | None = None) -> list[ModelT]:
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return list(db.scalars(stmt).all())

    def get(self, db: Session, entity_id: Any) -> ModelT | None:
        return db.get(self.model, entity_id)

    def create(self, db: Session, entity: ModelT) -> ModelT:
        return self._save(db, entity)

    def update_fields(self, db: Session, entity: ModelT, data: dict[str, Any]) -> ModelT:
        for key, value in data.items():
            setattr(entity, key, value)
        db.add(entity)
        db.flush()
        return entity

    def delete(self, db: Session, entity: ModelT) -> None:
        db.delete(entity)
        db.flush()

    def _save(self, db: Session, entity: EntityT) -> EntityT:
        db.add(entity)
        db.flush()
        db.refresh(entity)
        return entity

    def _save_many(self, db: Session, entities: list[EntityT]) -> list[EntityT]:
        db.add_all(entities)
        db.flush()
        return entities

    def _paginate_query(
        self,
        db: Session,
        stmt: Any,
        params: PaginationParams,
    ) -> tuple[list[Any], int]:
        total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
        items = list(
            db.scalars(
                stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)
            ).all()
        )
        return items, int(total)
