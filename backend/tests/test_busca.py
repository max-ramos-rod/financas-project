import uuid


def _setup_user(client):
    email = f"busca_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "senha123", "nome": "Busca Teste", "role": "user"},
    )
    res = client.post("/api/v1/auth/login", data={"username": email, "password": "senha123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_busca_requires_auth(client):
    res = client.get("/api/v1/busca", params={"q": "teste"})
    assert res.status_code == 401


def test_busca_termo_muito_curto(client):
    headers = _setup_user(client)
    res = client.get("/api/v1/busca", params={"q": "a"}, headers=headers)
    assert res.status_code == 422


def test_busca_retorna_estrutura_correta(client):
    headers = _setup_user(client)
    res = client.get("/api/v1/busca", params={"q": "xyz"}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "query" in body
    assert "transacoes" in body
    assert "contas" in body
    assert body["query"] == "xyz"


def test_busca_isolamento_entre_usuarios(client):
    headers_a = _setup_user(client)
    headers_b = _setup_user(client)

    conta_res = client.post(
        "/api/v1/contas",
        json={"nome": "Conta Secreta XYZ", "tipo": "conta_corrente", "cor": "#aabbcc", "saldo": 100.0},
        headers=headers_a,
    )
    assert conta_res.status_code == 201

    res = client.get("/api/v1/busca", params={"q": "Secreta"}, headers=headers_b)
    assert res.status_code == 200
    assert res.json()["contas"] == []


def test_busca_encontra_conta_propria(client):
    headers = _setup_user(client)
    client.post(
        "/api/v1/contas",
        json={"nome": "Minha Conta Especial", "tipo": "conta_corrente", "cor": "#aabbcc", "saldo": 500.0},
        headers=headers,
    )

    res = client.get("/api/v1/busca", params={"q": "Especial"}, headers=headers)
    assert res.status_code == 200
    contas = res.json()["contas"]
    assert any("Especial" in c["nome"] for c in contas)
