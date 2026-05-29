from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models import Conta


class ContaRepositoryProtocol(Protocol):
    def get(self, db: Session, entity_id: Any) -> Conta | None: ...
    def create(self, db: Session, entity: Conta) -> Conta: ...
    def delete(self, db: Session, entity: Conta) -> None: ...
    def _save(self, db: Session, entity: Conta) -> Conta: ...
