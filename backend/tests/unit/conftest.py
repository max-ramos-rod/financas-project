import os
import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.models import (  # noqa: E402
    Categoria,
    Conta,
    Delegacao,
    DelegacaoStatus,
    Meta,
    Orcamento,
    StatusLiquidacao,
    TipoConta,
    TipoTransacao,
)
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


def make_meta(id: int = 1, user_id: int = 1) -> Meta:
    meta = Meta()
    meta.id = id
    meta.user_id = user_id
    meta.nome = "Meta Teste"
    meta.valor_alvo = 1000.0
    meta.valor_atual = 0.0
    meta.data_inicio = date(2024, 1, 1)
    return meta


def make_orcamento(id: int = 1, user_id: int = 1) -> Orcamento:
    orcamento = Orcamento()
    orcamento.id = id
    orcamento.user_id = user_id
    orcamento.categoria_id = 1
    orcamento.mes = 1
    orcamento.ano = 2024
    orcamento.valor_planejado = 500.0
    orcamento.valor_gasto = 0.0
    return orcamento


def make_categoria(id: int = 1, user_id: int = 1, padrao: bool = False) -> Categoria:
    cat = Categoria()
    cat.id = id
    cat.user_id = user_id
    cat.nome = "Alimentação"
    cat.tipo = TipoTransacao.SAIDA
    cat.padrao = padrao
    cat.icone = None
    cat.cor = "#6B7280"
    return cat


def make_delegacao(
    id: int = 1,
    owner_user_id: int = 1,
    delegate_user_id: int = 2,
    status: DelegacaoStatus = DelegacaoStatus.PENDING,
) -> Delegacao:
    from datetime import datetime, timedelta, timezone

    d = Delegacao()
    d.id = id
    d.owner_user_id = owner_user_id
    d.delegate_user_id = delegate_user_id
    d.invited_email = "delegate@example.com"
    d.invite_token = "test-token-abc"
    d.invite_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    d.status = status
    d.can_write = True
    d.accepted_at = None
    d.revoked_at = None
    return d


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
