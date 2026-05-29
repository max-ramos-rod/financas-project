from unittest.mock import MagicMock

import pytest

from app.models import Categoria, TipoTransacao
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate
from app.services.categoria import CategoriaService

from .conftest import make_categoria

USER_ID = 1


class FakeCategoriaRepository:
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
    repo = FakeCategoriaRepository()
    svc = CategoriaService(repo=repo)
    return svc, repo


def _make_db(*first_returns):
    """MagicMock db whose .query().filter().first() pops values from first_returns in order."""
    db = MagicMock()
    if len(first_returns) == 1:
        db.query.return_value.filter.return_value.first.return_value = first_returns[0]
    else:
        db.query.return_value.filter.return_value.first.side_effect = list(first_returns)
    return db


def _make_cat_create(**kwargs) -> CategoriaCreate:
    defaults = dict(nome="Mercado", icone=None, cor="#6B7280", tipo=TipoTransacao.SAIDA, padrao=False)
    defaults.update(kwargs)
    return CategoriaCreate(**defaults)


class TestCriar:
    def test_cria_e_retorna_categoria(self):
        svc, repo = _service()
        db = _make_db(None)  # no duplicate
        result = svc.criar(db, _make_cat_create(), USER_ID)
        assert isinstance(result, Categoria)
        assert result.nome == "Mercado"

    def test_nome_duplicado_levanta_erro(self):
        svc, repo = _service()
        db = _make_db(make_categoria())  # duplicate found
        with pytest.raises(ValueError, match="Ja existe categoria"):
            svc.criar(db, _make_cat_create(), USER_ID)

    def test_commit_chamado(self):
        svc, repo = _service()
        db = _make_db(None)
        svc.criar(db, _make_cat_create(), USER_ID)
        db.commit.assert_called_once()

    def test_categoria_salva_no_repo(self):
        svc, repo = _service()
        db = _make_db(None)
        svc.criar(db, _make_cat_create(), USER_ID)
        assert len(repo.saved) == 1


class TestAtualizar:
    def test_nao_encontrada_retorna_none(self):
        svc, repo = _service()
        db = _make_db(None)
        result = svc.atualizar(db, 99, USER_ID, CategoriaUpdate(nome="X"))
        assert result is None

    def test_padrao_levanta_erro(self):
        cat = make_categoria(padrao=True)
        svc, repo = _service()
        db = _make_db(cat)
        with pytest.raises(ValueError, match="padrao"):
            svc.atualizar(db, cat.id, USER_ID, CategoriaUpdate(nome="Novo"))

    def test_atualiza_campos(self):
        cat = make_categoria()
        svc, repo = _service()
        db = _make_db(cat)
        # _nome_tipo_duplicado with ignorar_id uses .filter().filter().first()
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc.atualizar(db, cat.id, USER_ID, CategoriaUpdate(nome="Farmácia"))
        assert cat.nome == "Farmácia"

    def test_commit_chamado(self):
        cat = make_categoria()
        svc, repo = _service()
        db = _make_db(cat)
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        svc.atualizar(db, cat.id, USER_ID, CategoriaUpdate(nome="X"))
        db.commit.assert_called_once()


class TestDeletar:
    def test_nao_encontrada_retorna_false(self):
        svc, repo = _service()
        db = _make_db(None)
        assert svc.deletar(db, 99, USER_ID) is False

    def test_padrao_levanta_erro(self):
        cat = make_categoria(padrao=True)
        svc, repo = _service()
        db = _make_db(cat)
        with pytest.raises(ValueError, match="padrao"):
            svc.deletar(db, cat.id, USER_ID)

    def test_em_uso_levanta_erro(self):
        from unittest.mock import MagicMock as MM
        cat = make_categoria()
        svc, repo = _service()
        transacao_mock = MM()
        # first .first() → cat; second .first() → transacao (in use)
        db = _make_db(cat, transacao_mock)
        with pytest.raises(ValueError, match="em uso"):
            svc.deletar(db, cat.id, USER_ID)

    def test_deleta_e_retorna_true(self):
        cat = make_categoria()
        repo = FakeCategoriaRepository()
        repo._save(None, cat)
        svc = CategoriaService(repo=repo)
        # first .first() → cat; second .first() → None (not in use)
        db = _make_db(cat, None)
        result = svc.deletar(db, cat.id, USER_ID)
        assert result is True
        assert len(repo.saved) == 0

    def test_commit_chamado(self):
        cat = make_categoria()
        repo = FakeCategoriaRepository()
        repo._save(None, cat)
        svc = CategoriaService(repo=repo)
        db = _make_db(cat, None)
        svc.deletar(db, cat.id, USER_ID)
        db.commit.assert_called_once()
