from unittest.mock import MagicMock

import pytest

from app.models import Conta, TipoConta
from app.schemas.conta import ContaCreate, ContaUpdate
from app.services.conta import ContaService

from .conftest import FakeTransacaoRepository, make_conta

USER_ID = 1


class FakeContaRepository:
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

    @property
    def saved(self):
        return list(self._store)


def _service():
    repo = FakeContaRepository()
    svc = ContaService(repo=repo)
    return svc, repo


def _make_db(conta=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = conta
    return db


def _make_conta_create(**kwargs) -> ContaCreate:
    defaults = dict(
        nome="Conta Teste",
        tipo=TipoConta.CONTA_CORRENTE,
        saldo=500.0,
        moeda="BRL",
        instituicao=None,
        cor="#3b82f6",
        icone="wallet",
        dia_fechamento=None,
        dia_vencimento=None,
        limite_credito=None,
    )
    defaults.update(kwargs)
    return ContaCreate(**defaults)


class TestCriar:
    def test_cria_e_retorna_conta(self):
        svc, repo = _service()
        db = _make_db()
        cc = _make_conta_create(nome="Nubank", saldo=100.0)
        result = svc.criar(db, cc, USER_ID)
        assert isinstance(result, Conta)
        assert result.nome == "Nubank"

    def test_cartao_credito_zera_saldo(self):
        svc, repo = _service()
        db = _make_db()
        cc = _make_conta_create(
            tipo=TipoConta.CARTAO_CREDITO,
            saldo=999.0,
            dia_fechamento=10,
            dia_vencimento=20,
        )
        result = svc.criar(db, cc, USER_ID)
        assert result.saldo == 0.0

    def test_commit_chamado(self):
        svc, repo = _service()
        db = _make_db()
        svc.criar(db, _make_conta_create(), USER_ID)
        db.commit.assert_called_once()

    def test_conta_salva_no_repo(self):
        svc, repo = _service()
        db = _make_db()
        svc.criar(db, _make_conta_create(), USER_ID)
        assert len(repo.saved) == 1


class TestAtualizar:
    def test_nao_encontrada_retorna_none(self):
        svc, repo = _service()
        db = _make_db(conta=None)
        result = svc.atualizar(db, 99, USER_ID, ContaUpdate(nome="X"))
        assert result is None

    def test_nao_cartao_limpa_campos_cartao(self):
        conta = make_conta(tipo=TipoConta.CONTA_CORRENTE)
        conta.dia_fechamento = 10
        conta.dia_vencimento = 20
        conta.limite_credito = 5000.0
        svc, repo = _service()
        db = _make_db(conta=conta)
        svc.atualizar(db, conta.id, USER_ID, ContaUpdate(nome="Novo"))
        assert conta.dia_fechamento is None
        assert conta.dia_vencimento is None
        assert conta.limite_credito is None

    def test_cartao_sem_fechamento_levanta_erro(self):
        conta = make_conta(tipo=TipoConta.CARTAO_CREDITO)
        conta.dia_fechamento = None
        conta.dia_vencimento = None
        svc, repo = _service()
        db = _make_db(conta=conta)
        with pytest.raises(ValueError, match="dia_fechamento"):
            svc.atualizar(db, conta.id, USER_ID, ContaUpdate(tipo=TipoConta.CARTAO_CREDITO, dia_vencimento=20))

    def test_cartao_fechamento_igual_vencimento_levanta_erro(self):
        conta = make_conta(tipo=TipoConta.CARTAO_CREDITO)
        conta.dia_fechamento = 10
        conta.dia_vencimento = 10
        svc, repo = _service()
        db = _make_db(conta=conta)
        with pytest.raises(ValueError, match="nao podem ser iguais"):
            svc.atualizar(db, conta.id, USER_ID, ContaUpdate(dia_fechamento=10, dia_vencimento=10))

    def test_cartao_zera_saldo_no_update(self):
        conta = make_conta(tipo=TipoConta.CARTAO_CREDITO)
        conta.dia_fechamento = 10
        conta.dia_vencimento = 20
        svc, repo = _service()
        db = _make_db(conta=conta)
        svc.atualizar(db, conta.id, USER_ID, ContaUpdate(nome="Card"))
        assert conta.saldo == 0.0

    def test_commit_chamado(self):
        conta = make_conta()
        conta.dia_fechamento = None
        conta.dia_vencimento = None
        conta.limite_credito = None
        svc, repo = _service()
        db = _make_db(conta=conta)
        svc.atualizar(db, conta.id, USER_ID, ContaUpdate(nome="Novo"))
        db.commit.assert_called_once()


class TestDeletar:
    def test_nao_encontrada_retorna_false(self):
        svc, repo = _service()
        db = _make_db(conta=None)
        assert svc.deletar(db, 99, USER_ID) is False

    def test_deleta_e_retorna_true(self):
        conta = make_conta()
        repo = FakeContaRepository()
        repo._save(None, conta)
        svc = ContaService(repo=repo)
        db = _make_db(conta=conta)
        result = svc.deletar(db, conta.id, USER_ID)
        assert result is True
        assert len(repo.saved) == 0

    def test_commit_chamado(self):
        conta = make_conta()
        repo = FakeContaRepository()
        repo._save(None, conta)
        svc = ContaService(repo=repo)
        db = _make_db(conta=conta)
        svc.deletar(db, conta.id, USER_ID)
        db.commit.assert_called_once()


class TestPagarFatura:
    def _resumo(self):
        from datetime import date
        from unittest.mock import MagicMock
        r = MagicMock()
        r.periodo_inicio = date(2024, 1, 1)
        r.periodo_fim = date(2024, 1, 31)
        return r

    def _payload(self, conta_pagamento_id=2):
        from app.schemas.conta import PagarFaturaRequest
        return PagarFaturaRequest(conta_pagamento_id=conta_pagamento_id)

    def test_conta_nao_encontrada_levanta_erro(self):
        svc, _ = _service()
        db = _make_db(conta=None)
        with pytest.raises(ValueError, match="Conta nao encontrada"):
            svc.pagar_fatura(db, 1, USER_ID, self._payload(), self._resumo())

    def test_nao_cartao_levanta_erro(self):
        conta = make_conta(tipo=TipoConta.CONTA_CORRENTE)
        svc, _ = _service()
        db = _make_db(conta=conta)
        with pytest.raises(ValueError, match="nao e cartao"):
            svc.pagar_fatura(db, conta.id, USER_ID, self._payload(), self._resumo())

    def test_conta_pagamento_nao_encontrada_levanta_erro(self):
        conta_cartao = make_conta(tipo=TipoConta.CARTAO_CREDITO)
        svc, _ = _service()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [conta_cartao, None]
        with pytest.raises(ValueError, match="pagamento nao encontrada"):
            svc.pagar_fatura(db, conta_cartao.id, USER_ID, self._payload(), self._resumo())

    def test_conta_pagamento_igual_cartao_levanta_erro(self):
        conta_cartao = make_conta(id=1, tipo=TipoConta.CARTAO_CREDITO)
        svc, _ = _service()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [conta_cartao, conta_cartao]
        with pytest.raises(ValueError, match="diferente do cartao"):
            svc.pagar_fatura(db, conta_cartao.id, USER_ID, self._payload(conta_pagamento_id=1), self._resumo())

    def test_conta_pagamento_cartao_levanta_erro(self):
        conta_cartao = make_conta(id=1, tipo=TipoConta.CARTAO_CREDITO)
        conta_pagamento = make_conta(id=2, tipo=TipoConta.CARTAO_CREDITO)
        svc, _ = _service()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [conta_cartao, conta_pagamento]
        with pytest.raises(ValueError, match="sair de conta nao cartao"):
            svc.pagar_fatura(db, conta_cartao.id, USER_ID, self._payload(), self._resumo())
