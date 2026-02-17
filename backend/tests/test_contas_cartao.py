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


def _auth_headers(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    register_response = _register_user(client, email)
    assert register_response.status_code == 201
    login_response = _login_user(client, email)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_cartao_credito_forces_saldo_zero(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Cartao XPTO",
            "tipo": "cartao_credito",
            "saldo": 999.99,
            "dia_fechamento": 20,
            "dia_vencimento": 28,
            "limite_credito": 5000,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["tipo"] == "cartao_credito"
    assert payload["saldo"] == 0


def test_update_to_cartao_credito_forces_saldo_zero(client):
    headers = _auth_headers(client)

    create_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Corrente Teste",
            "tipo": "conta_corrente",
            "saldo": 123.45,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert create_response.status_code == 201
    conta_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/contas/{conta_id}",
        headers=headers,
        json={
            "tipo": "cartao_credito",
            "saldo": 777.77,
            "dia_fechamento": 22,
            "dia_vencimento": 29,
            "limite_credito": 4000,
        },
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["tipo"] == "cartao_credito"
    assert payload["saldo"] == 0
