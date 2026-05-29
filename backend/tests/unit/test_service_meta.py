from datetime import date
from unittest.mock import MagicMock

from app.models import Meta
from app.schemas.meta import MetaCreate, MetaUpdate
from app.services.meta import MetaService

from .conftest import make_meta

USER_ID = 1


class FakeMetaRepository:
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
    repo = FakeMetaRepository()
    svc = MetaService(repo=repo)
    return svc, repo


def _make_db(meta=None):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = meta
    return db


def _make_meta_create(**kwargs) -> MetaCreate:
    defaults = dict(
        nome="Meta Teste",
        descricao=None,
        valor_alvo=1000.0,
        valor_atual=0.0,
        data_inicio=date(2024, 1, 1),
        data_fim=None,
        concluida=False,
        cor="#10B981",
    )
    defaults.update(kwargs)
    return MetaCreate(**defaults)


class TestCriar:
    def test_cria_e_retorna_meta(self):
        svc, repo = _service()
        db = _make_db()
        result = svc.criar(db, _make_meta_create(nome="Viagem"), USER_ID)
        assert isinstance(result, Meta)
        assert result.nome == "Viagem"

    def test_commit_chamado(self):
        svc, repo = _service()
        db = _make_db()
        svc.criar(db, _make_meta_create(), USER_ID)
        db.commit.assert_called_once()

    def test_meta_salva_no_repo(self):
        svc, repo = _service()
        db = _make_db()
        svc.criar(db, _make_meta_create(), USER_ID)
        assert len(repo.saved) == 1


class TestAtualizar:
    def test_nao_encontrada_retorna_none(self):
        svc, repo = _service()
        db = _make_db(meta=None)
        result = svc.atualizar(db, 99, USER_ID, MetaUpdate(nome="X"))
        assert result is None

    def test_atualiza_campos(self):
        meta = make_meta()
        svc, repo = _service()
        db = _make_db(meta=meta)
        svc.atualizar(db, meta.id, USER_ID, MetaUpdate(nome="Novo Nome"))
        assert meta.nome == "Novo Nome"

    def test_commit_chamado(self):
        meta = make_meta()
        svc, repo = _service()
        db = _make_db(meta=meta)
        svc.atualizar(db, meta.id, USER_ID, MetaUpdate(nome="X"))
        db.commit.assert_called_once()


class TestDeletar:
    def test_nao_encontrada_retorna_false(self):
        svc, repo = _service()
        db = _make_db(meta=None)
        assert svc.deletar(db, 99, USER_ID) is False

    def test_deleta_e_retorna_true(self):
        meta = make_meta()
        repo = FakeMetaRepository()
        repo._save(None, meta)
        svc = MetaService(repo=repo)
        db = _make_db(meta=meta)
        result = svc.deletar(db, meta.id, USER_ID)
        assert result is True
        assert len(repo.saved) == 0

    def test_commit_chamado(self):
        meta = make_meta()
        repo = FakeMetaRepository()
        repo._save(None, meta)
        svc = MetaService(repo=repo)
        db = _make_db(meta=meta)
        svc.deletar(db, meta.id, USER_ID)
        db.commit.assert_called_once()
