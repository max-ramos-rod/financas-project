from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models import Orcamento


class OrcamentoRepositoryProtocol(Protocol):
    def get(self, db: Session, entity_id: Any) -> Orcamento | None: ...
    def create(self, db: Session, entity: Orcamento) -> Orcamento: ...
    def delete(self, db: Session, entity: Orcamento) -> None: ...
    def _save(self, db: Session, entity: Orcamento) -> Orcamento: ...
