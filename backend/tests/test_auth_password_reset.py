import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.db.session import get_db
from app.main import app


def _unique_email():
    return f"user_{uuid.uuid4().hex[:8]}@example.com"


def _register_and_login(client, email: str, password: str = "senha123"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "nome": "Teste", "role": "user"},
    )
    r = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return r.json().get("access_token")


# ---------------------------------------------------------------------------
# forgot-password
# ---------------------------------------------------------------------------

def test_forgot_password_email_existente(client):
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "senha123", "nome": "Teste", "role": "user"},
    )
    r = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert r.status_code == 200
    assert "message" in r.json()


def test_forgot_password_email_inexistente_retorna_mesmo_200(client):
    r = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "naoexiste@example.com"},
    )
    assert r.status_code == 200
    assert "message" in r.json()


def test_forgot_password_mesma_mensagem_independente_de_existencia(client):
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "senha123", "nome": "Teste", "role": "user"},
    )
    r_existe = client.post("/api/v1/auth/forgot-password", json={"email": email})
    r_nao_existe = client.post(
        "/api/v1/auth/forgot-password", json={"email": "fantasma@example.com"}
    )
    assert r_existe.json()["message"] == r_nao_existe.json()["message"]


# ---------------------------------------------------------------------------
# reset-password
# ---------------------------------------------------------------------------

def _criar_token_para(client, email: str, password: str = "senha123") -> str:
    """Registra usuário e retorna um token de reset válido via CRUD direto."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "nome": "Teste", "role": "user"},
    )
    # Busca o user_id via forgot-password (cria token via endpoint)
    client.post("/api/v1/auth/forgot-password", json={"email": email})
    # Recupera o token diretamente do DB de testes
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    from app.models.password_reset_token import PasswordResetToken
    token_obj = db.query(PasswordResetToken).order_by(PasswordResetToken.id.desc()).first()
    db.close()
    return token_obj.token


def test_reset_password_token_valido(client):
    email = _unique_email()
    token = _criar_token_para(client, email)

    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "novaSenha456"},
    )
    assert r.status_code == 200
    assert "message" in r.json()


def test_login_apos_reset(client):
    email = _unique_email()
    token = _criar_token_para(client, email)

    client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "novaSenha456"},
    )
    r = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "novaSenha456"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_com_senha_antiga_falha_apos_reset(client):
    email = _unique_email()
    token = _criar_token_para(client, email, password="senhaAntiga")

    client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "senhaNova"},
    )
    r = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "senhaAntiga"},
    )
    assert r.status_code == 401


def test_reset_password_token_invalido(client):
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "tokeninvalido", "password": "qualquer"},
    )
    assert r.status_code == 400


def test_reset_password_token_ja_usado(client):
    email = _unique_email()
    token = _criar_token_para(client, email)

    client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "primeiraTroca"},
    )
    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "segundaTroca"},
    )
    assert r.status_code == 400


def test_reset_password_token_expirado(client):
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "senha123", "nome": "Teste", "role": "user"},
    )
    # Cria token expirado diretamente no DB
    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user import User
    user = db.query(User).filter(User.email == email).first()
    token_obj = PasswordResetToken(
        user_id=user.id,
        token="token_expirado_12345",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db.add(token_obj)
    db.commit()
    db.close()

    r = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "token_expirado_12345", "password": "qualquer"},
    )
    assert r.status_code == 400
