import uuid


def _register_user(client, email: str, password: str = "senha123"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "nome": "Usuario Teste",
            "role": "user",
        },
    )


def _login_user(client, email: str, password: str = "senha123"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def test_login_returns_access_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    register_response = _register_user(client, email)
    assert register_response.status_code == 201

    login_response = _login_user(client, email)
    assert login_response.status_code == 200

    payload = login_response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


def test_protected_endpoint_requires_valid_token(client):
    invalid_response = client.get(
        "/api/v1/contas",
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert invalid_response.status_code == 401

    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    _register_user(client, email)
    login_response = _login_user(client, email)
    token = login_response.json()["access_token"]

    valid_response = client.get(
        "/api/v1/contas",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert valid_response.status_code == 200
    assert isinstance(valid_response.json(), list)
