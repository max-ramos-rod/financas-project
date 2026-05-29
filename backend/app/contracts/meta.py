from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models import Meta


class MetaRepositoryProtocol(Protocol):
    def get(self, db: Session, entity_id: Any) -> Meta | None: ...
    def create(self, db: Session, entity: Meta) -> Meta: ...
    def delete(self, db: Session, entity: Meta) -> None: ...
    def _save(self, db: Session, entity: Meta) -> Meta: ...
