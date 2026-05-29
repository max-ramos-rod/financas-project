import uuid

import pytest

from app.core.limiter import limiter


@pytest.fixture
def client_with_limiter(client):
    """Cliente com rate limiting habilitado."""
    limiter.enabled = True
    yield client
    limiter.enabled = False


def test_login_rate_limit(client_with_limiter):
    client = client_with_limiter
    email = f"rl_{uuid.uuid4().hex[:8]}@example.com"
    status_codes = []
    for _ in range(21):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": "wrongpassword"},
        )
        status_codes.append(r.status_code)
    # Primeiros 20 são 401 (credenciais inválidas), o 21º deve ser 429
    assert status_codes[:20] == [401] * 20
    assert status_codes[20] == 429


def test_forgot_password_rate_limit(client_with_limiter):
    client = client_with_limiter
    email = f"rl_{uuid.uuid4().hex[:8]}@example.com"
    status_codes = []
    for _ in range(4):
        r = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        status_codes.append(r.status_code)
    # Primeiros 3 devem ser 200, o 4º deve ser 429
    assert status_codes[:3] == [200, 200, 200]
    assert status_codes[3] == 429
