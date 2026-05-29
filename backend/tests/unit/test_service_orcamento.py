from unittest.mock import MagicMock

from app.models import Orcamento
from app.schemas.orcamento import OrcamentoCreate, OrcamentoUpdate
from app.services.orcamento import OrcamentoService

from .conftest import make_orcamento

USER_ID = 1


class FakeOrcamentoRepository:
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
    repo = FakeOrcamentoRepository()
    svc = OrcamentoService(repo=repo)
    return svc, repo


def _make_db(orcamento=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = orcamento
    db.query.return_value.filter.return_value.all.return_value = []
    return db


def _make_orcamento_create(**kwargs) -> OrcamentoCreate:
    defaults = dict(
        categoria_id=1,
        mes=1,
        ano=2024,
        valor_planejado=500.0,
    )
    defaults.update(kwargs)
    return OrcamentoCreate(**defaults)


class TestCriar:
    def test_cria_e_retorna_orcamento(self):
        svc, repo = _service()
        db = _make_db()
        result = svc.criar(db, _make_orcamento_create(), USER_ID)
        assert isinstance(result, Orcamento)
        assert result.valor_planejado == 500.0

    def test_valor_gasto_zero_sem_transacoes(self):
        svc, repo = _service()
        db = _make_db()
        result = svc.criar(db, _make_orcamento_create(), USER_ID)
        assert result.valor_gasto == 0.0

    def test_commit_chamado(self):
        svc, repo = _service()
        db = _make_db()
        svc.criar(db, _make_orcamento_create(), USER_ID)
        db.commit.assert_called_once()

    def test_orcamento_salvo_no_repo(self):
        svc, repo = _service()
        db = _make_db()
        svc.criar(db, _make_orcamento_create(), USER_ID)
        assert len(repo.saved) == 1


class TestAtualizar:
    def test_nao_encontrado_retorna_none(self):
        svc, repo = _service()
        db = _make_db(orcamento=None)
        result = svc.atualizar(db, 99, USER_ID, OrcamentoUpdate(valor_planejado=999.0))
        assert result is None

    def test_atualiza_campos(self):
        orcamento = make_orcamento()
        svc, repo = _service()
        db = _make_db(orcamento=orcamento)
        svc.atualizar(db, orcamento.id, USER_ID, OrcamentoUpdate(valor_planejado=1000.0))
        assert orcamento.valor_planejado == 1000.0

    def test_commit_chamado(self):
        orcamento = make_orcamento()
        svc, repo = _service()
        db = _make_db(orcamento=orcamento)
        svc.atualizar(db, orcamento.id, USER_ID, OrcamentoUpdate(valor_planejado=200.0))
        db.commit.assert_called_once()


class TestDeletar:
    def test_nao_encontrado_retorna_false(self):
        svc, repo = _service()
        db = _make_db(orcamento=None)
        assert svc.deletar(db, 99, USER_ID) is False

    def test_deleta_e_retorna_true(self):
        orcamento = make_orcamento()
        repo = FakeOrcamentoRepository()
        repo._save(None, orcamento)
        svc = OrcamentoService(repo=repo)
        db = _make_db(orcamento=orcamento)
        result = svc.deletar(db, orcamento.id, USER_ID)
        assert result is True
        assert len(repo.saved) == 0

    def test_commit_chamado(self):
        orcamento = make_orcamento()
        repo = FakeOrcamentoRepository()
        repo._save(None, orcamento)
        svc = OrcamentoService(repo=repo)
        db = _make_db(orcamento=orcamento)
        svc.deletar(db, orcamento.id, USER_ID)
        db.commit.assert_called_once()
