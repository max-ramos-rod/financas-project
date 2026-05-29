from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.models import Delegacao, DelegacaoStatus
from app.schemas.delegacao import DelegacaoConfirmRequest
from app.services.delegacao import DelegacaoService

from .conftest import make_delegacao

OWNER_ID = 1
INVITED_EMAIL = "delegate@example.com"


class FakeDelegacaoRepository:
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
    repo = FakeDelegacaoRepository()
    svc = DelegacaoService(repo=repo)
    return svc, repo


def _make_db(*first_returns):
    db = MagicMock()
    if len(first_returns) == 1:
        db.query.return_value.filter.return_value.first.return_value = first_returns[0]
    else:
        db.query.return_value.filter.return_value.first.side_effect = list(first_returns)
    return db


class TestInvite:
    def test_cria_novo_convite_sem_usuario_existente(self):
        svc, repo = _service()
        # first .first() → no User; second .first() → no existing Delegacao
        db = _make_db(None, None)
        delegacao, has_account = svc.invite(db, OWNER_ID, INVITED_EMAIL, can_write=True)
        assert isinstance(delegacao, Delegacao)
        assert has_account is False
        assert delegacao.invited_email == INVITED_EMAIL

    def test_cria_novo_convite_com_usuario_existente(self):
        svc, repo = _service()
        user_mock = MagicMock()
        user_mock.id = 5
        db = _make_db(user_mock, None)  # User found, no existing delegacao
        delegacao, has_account = svc.invite(db, OWNER_ID, INVITED_EMAIL, can_write=True)
        assert has_account is True
        assert delegacao.delegate_user_id == 5

    def test_reenvia_convite_existente_pendente(self):
        svc, repo = _service()
        existing = make_delegacao(status=DelegacaoStatus.PENDING)
        db = _make_db(None, existing)  # no user, existing delegacao
        delegacao, _ = svc.invite(db, OWNER_ID, INVITED_EMAIL, can_write=False)
        assert delegacao is existing
        assert delegacao.can_write is False

    def test_ativo_levanta_erro(self):
        svc, repo = _service()
        active = make_delegacao(status=DelegacaoStatus.ACTIVE)
        db = _make_db(None, active)
        with pytest.raises(ValueError, match="ativa"):
            svc.invite(db, OWNER_ID, INVITED_EMAIL, can_write=True)

    def test_commit_chamado(self):
        svc, repo = _service()
        db = _make_db(None, None)
        svc.invite(db, OWNER_ID, INVITED_EMAIL, can_write=True)
        db.commit.assert_called_once()


class TestAccept:
    def test_aceita_pendente(self):
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING)
        svc, repo = _service()
        db = MagicMock()
        result = svc.accept(db, delegacao)
        assert result.status == DelegacaoStatus.ACTIVE
        assert result.invite_token is None

    def test_nao_pendente_levanta_erro(self):
        delegacao = make_delegacao(status=DelegacaoStatus.ACTIVE)
        svc, _ = _service()
        with pytest.raises(ValueError, match="pendentes"):
            svc.accept(MagicMock(), delegacao)

    def test_expirado_levanta_erro(self):
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING)
        delegacao.invite_expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        svc, _ = _service()
        with pytest.raises(ValueError, match="expirado"):
            svc.accept(MagicMock(), delegacao)

    def test_sem_delegate_levanta_erro(self):
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING, delegate_user_id=None)
        svc, _ = _service()
        with pytest.raises(ValueError, match="sem usuario"):
            svc.accept(MagicMock(), delegacao)

    def test_commit_chamado(self):
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING)
        svc, _ = _service()
        db = MagicMock()
        svc.accept(db, delegacao)
        db.commit.assert_called_once()


class TestRevoke:
    def test_revoga_delegacao(self):
        delegacao = make_delegacao(status=DelegacaoStatus.ACTIVE)
        svc, _ = _service()
        db = MagicMock()
        result = svc.revoke(db, delegacao)
        assert result.status == DelegacaoStatus.REVOKED
        assert result.invite_token is None

    def test_commit_chamado(self):
        delegacao = make_delegacao(status=DelegacaoStatus.ACTIVE)
        svc, _ = _service()
        db = MagicMock()
        svc.revoke(db, delegacao)
        db.commit.assert_called_once()


class TestConfirm:
    def test_delegate_ja_associado_aceita_direto(self):
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING, delegate_user_id=2)
        svc, _ = _service()
        db = MagicMock()
        result = svc.confirm(db, delegacao, DelegacaoConfirmRequest())
        assert result.status == DelegacaoStatus.ACTIVE

    @patch("app.services.delegacao.get_user_by_email")
    def test_usuario_existente_por_email_associado(self, mock_get_user):
        user_mock = MagicMock()
        user_mock.id = 9
        mock_get_user.return_value = user_mock
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING, delegate_user_id=None)
        svc, _ = _service()
        db = MagicMock()
        result = svc.confirm(db, delegacao, DelegacaoConfirmRequest())
        assert delegacao.delegate_user_id == 9
        assert result.status == DelegacaoStatus.ACTIVE

    @patch("app.services.delegacao.create_user")
    @patch("app.services.delegacao.get_user_by_email")
    def test_novo_usuario_criado(self, mock_get_user, mock_create_user):
        mock_get_user.return_value = None
        new_user = MagicMock()
        new_user.id = 10
        mock_create_user.return_value = new_user
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING, delegate_user_id=None)
        svc, _ = _service()
        db = MagicMock()
        payload = DelegacaoConfirmRequest(nome="Novo User", password="senha123")
        result = svc.confirm(db, delegacao, payload)
        assert delegacao.delegate_user_id == 10
        assert result.status == DelegacaoStatus.ACTIVE

    @patch("app.services.delegacao.get_user_by_email")
    def test_sem_nome_senha_levanta_erro(self, mock_get_user):
        mock_get_user.return_value = None
        delegacao = make_delegacao(status=DelegacaoStatus.PENDING, delegate_user_id=None)
        svc, _ = _service()
        with pytest.raises(ValueError, match="obrigatorios"):
            svc.confirm(MagicMock(), delegacao, DelegacaoConfirmRequest())
