from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models import Delegacao


class DelegacaoRepositoryProtocol(Protocol):
    def get(self, db: Session, entity_id: Any) -> Delegacao | None: ...
    def create(self, db: Session, entity: Delegacao) -> Delegacao: ...
    def delete(self, db: Session, entity: Delegacao) -> None: ...
    def _save(self, db: Session, entity: Delegacao) -> Delegacao: ...
