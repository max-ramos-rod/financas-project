from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models import Categoria


class CategoriaRepositoryProtocol(Protocol):
    def get(self, db: Session, entity_id: Any) -> Categoria | None: ...
    def create(self, db: Session, entity: Categoria) -> Categoria: ...
    def delete(self, db: Session, entity: Categoria) -> None: ...
    def _save(self, db: Session, entity: Categoria) -> Categoria: ...
