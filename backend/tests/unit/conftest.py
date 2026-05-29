import os
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.models import Conta, StatusLiquidacao, TipoConta, TipoTransacao  # noqa: E402
from app.schemas.transacao import TransacaoCreate  # noqa: E402


class FakeTransacaoRepository:
    def __init__(self):
        self._store: list = []
        self._next_id = 1

    def get(self, db, entity_id):
        return next((e for e in self._store if e.id == entity_id), None)

    def create(self, db, entity):
        return self._save(db, entity)

    def delete(self, db, entity) -> None:
        self._store = [e for e in self._store if e is not entity]

    def _save(self, db, entity):
        if entity not in self._store:
            entity.id = self._next_id
            self._next_id += 1
            self._store.append(entity)
        return entity

    def _save_many(self, db, entities):
        for e in entities:
            if e not in self._store:
                e.id = self._next_id
                self._next_id += 1
                self._store.append(e)
        return entities

    @property
    def saved(self):
        return list(self._store)


def make_db(conta: Conta | None = None):
    """MagicMock session that returns `conta` from any db.query().filter().first() call."""
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = conta
    return db


def make_conta(
    id: int = 1,
    saldo: float = 1000.0,
    tipo: TipoConta = TipoConta.CONTA_CORRENTE,
    user_id: int = 1,
) -> Conta:
    conta = Conta()
    conta.id = id
    conta.user_id = user_id
    conta.saldo = saldo
    conta.tipo = tipo
    return conta


def make_transacao_create(**overrides) -> TransacaoCreate:
    defaults = dict(
        conta_id=1,
        categoria_id=1,
        descricao="Teste",
        valor=100.0,
        tipo=TipoTransacao.SAIDA,
        data=date(2024, 1, 15),
        data_vencimento=date(2024, 1, 20),
        data_liquidacao=None,
        status_liquidacao=StatusLiquidacao.PREVISTO,
        fixa=False,
        recorrente=False,
        confirmada=True,
        tem_dizimo=False,
        percentual_dizimo=10.0,
        parcelado=False,
        total_parcelas=None,
        e_emprestimo=False,
        pessoa_emprestimo=None,
        observacoes=None,
        tags=None,
        valor_multa=0.0,
        valor_juros=0.0,
        valor_desconto=0.0,
        meta_id=None,
    )
    defaults.update(overrides)
    return TransacaoCreate(**defaults)
