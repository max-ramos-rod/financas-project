from calendar import monthrange
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.contracts.orcamento import OrcamentoRepositoryProtocol
from app.domain.cartao_fatura import valor_efetivo_transacao
from app.models import Orcamento, StatusLiquidacao, TipoTransacao, Transacao
from app.repositories.orcamento import OrcamentoRepository
from app.schemas.orcamento import OrcamentoCreate, OrcamentoUpdate


class OrcamentoService:
    def __init__(self, repo: OrcamentoRepositoryProtocol | None = None) -> None:
        self._repo: OrcamentoRepositoryProtocol = repo if repo is not None else OrcamentoRepository()

    def _calcular_valor_gasto(self, db: Session, orcamento: Orcamento) -> float:
        inicio = date(orcamento.ano, orcamento.mes, 1)
        fim = date(orcamento.ano, orcamento.mes, monthrange(orcamento.ano, orcamento.mes)[1])
        transacoes = (
            db.query(Transacao)
            .filter(
                Transacao.user_id == orcamento.user_id,
                Transacao.categoria_id == orcamento.categoria_id,
                Transacao.tipo == TipoTransacao.SAIDA,
                Transacao.data >= inicio,
                Transacao.data <= fim,
                Transacao.status_liquidacao != StatusLiquidacao.CANCELADO,
            )
            .all()
        )
        return sum(valor_efetivo_transacao(t) for t in transacoes)

    def criar(self, db: Session, orcamento: OrcamentoCreate, user_id: int) -> Orcamento:
        db_orcamento = Orcamento(user_id=user_id, **orcamento.model_dump())
        self._repo._save(db, db_orcamento)
        db.commit()
        db.refresh(db_orcamento)
        db_orcamento.valor_gasto = self._calcular_valor_gasto(db, db_orcamento)
        return db_orcamento

    def atualizar(
        self,
        db: Session,
        orcamento_id: int,
        user_id: int,
        orcamento_update: OrcamentoUpdate,
    ) -> Optional[Orcamento]:
        db_orcamento = (
            db.query(Orcamento)
            .filter(Orcamento.id == orcamento_id, Orcamento.user_id == user_id)
            .first()
        )
        if not db_orcamento:
            return None
        for key, value in orcamento_update.model_dump(exclude_unset=True).items():
            setattr(db_orcamento, key, value)
        self._repo._save(db, db_orcamento)
        db.commit()
        db.refresh(db_orcamento)
        db_orcamento.valor_gasto = self._calcular_valor_gasto(db, db_orcamento)
        return db_orcamento

    def deletar(self, db: Session, orcamento_id: int, user_id: int) -> bool:
        db_orcamento = (
            db.query(Orcamento)
            .filter(Orcamento.id == orcamento_id, Orcamento.user_id == user_id)
            .first()
        )
        if not db_orcamento:
            return False
        self._repo.delete(db, db_orcamento)
        db.commit()
        return True
