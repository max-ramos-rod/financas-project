import uuid
from datetime import date


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


def _criar_conta(client, headers):
    response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Teste",
            "tipo": "conta_corrente",
            "saldo": 1000.0,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _criar_categoria(client, headers, nome: str):
    response = client.post(
        "/api/v1/categorias",
        headers=headers,
        json={
            "nome": nome,
            "icone": "tag",
            "cor": "#123ABC",
            "tipo": "saida",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _criar_transacao(
    client,
    headers,
    conta_id: int,
    descricao: str,
    valor: float,
    data_iso: str,
    categoria_id: int | None = None,
    tipo: str = "saida",
    fixa: bool = False,
    status_liquidacao: str = "previsto",
):
    payload = {
        "conta_id": conta_id,
        "descricao": descricao,
        "valor": valor,
        "tipo": tipo,
        "data": data_iso,
        "fixa": fixa,
        "status_liquidacao": status_liquidacao,
    }
    if categoria_id is not None:
        payload["categoria_id"] = categoria_id
    response = client.post("/api/v1/transacoes", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()


def test_filtro_categoria_sem_categoria(client):
    headers = _auth_headers(client)
    conta_id = _criar_conta(client, headers)
    categoria_id = _criar_categoria(client, headers, "Categoria Filtro")
    hoje = date.today().isoformat()

    sem_categoria = _criar_transacao(client, headers, conta_id, "Sem categoria", 80.0, hoje, categoria_id=None)
    _criar_transacao(client, headers, conta_id, "Com categoria", 90.0, hoje, categoria_id=categoria_id)

    response = client.get("/api/v1/transacoes?categoria_id=-1", headers=headers)
    assert response.status_code == 200
    items = response.json()
    ids = {item["id"] for item in items}
    assert sem_categoria["id"] in ids
    assert all(item.get("categoria_id") is None for item in items)


def test_filtro_fixas_e_nao_fixas(client):
    headers = _auth_headers(client)
    conta_id = _criar_conta(client, headers)
    hoje = date.today().isoformat()

    fixa = _criar_transacao(client, headers, conta_id, "Despesa fixa", 100.0, hoje, fixa=True)
    _criar_transacao(client, headers, conta_id, "Despesa variavel", 110.0, hoje, fixa=False)

    response = client.get("/api/v1/transacoes?fixa=fixas", headers=headers)
    assert response.status_code == 200
    items = response.json()
    ids = {item["id"] for item in items}
    assert fixa["id"] in ids
    assert all(item.get("fixa") is True for item in items)


def test_filtro_valor_modo_gte(client):
    headers = _auth_headers(client)
    conta_id = _criar_conta(client, headers)
    hoje = date.today().isoformat()

    maior = _criar_transacao(client, headers, conta_id, "Valor alto", 250.0, hoje)
    _criar_transacao(client, headers, conta_id, "Valor baixo", 40.0, hoje)

    response = client.get("/api/v1/transacoes?valor_modo=gte&valor_ref=200,00", headers=headers)
    assert response.status_code == 200
    items = response.json()
    ids = {item["id"] for item in items}
    assert maior["id"] in ids
    assert all(float(item["valor"]) >= 200.0 for item in items)


def test_filtro_orcamento_fora_e_dentro(client):
    headers = _auth_headers(client)
    conta_id = _criar_conta(client, headers)
    hoje = date.today()
    data_iso = hoje.isoformat()

    cat_estourada = _criar_categoria(client, headers, "Cat Estourada")
    cat_dentro = _criar_categoria(client, headers, "Cat Dentro")
    cat_sem_orcamento = _criar_categoria(client, headers, "Cat Sem Orcamento")

    create_orc_1 = client.post(
        "/api/v1/orcamentos",
        headers=headers,
        json={"categoria_id": cat_estourada, "mes": hoje.month, "ano": hoje.year, "valor_planejado": 100.0},
    )
    assert create_orc_1.status_code == 201

    create_orc_2 = client.post(
        "/api/v1/orcamentos",
        headers=headers,
        json={"categoria_id": cat_dentro, "mes": hoje.month, "ano": hoje.year, "valor_planejado": 500.0},
    )
    assert create_orc_2.status_code == 201

    fora_1 = _criar_transacao(client, headers, conta_id, "Estourou", 150.0, data_iso, categoria_id=cat_estourada)
    _criar_transacao(client, headers, conta_id, "Dentro", 100.0, data_iso, categoria_id=cat_dentro)
    fora_2 = _criar_transacao(client, headers, conta_id, "Sem orc", 60.0, data_iso, categoria_id=cat_sem_orcamento)

    response_fora = client.get(
        f"/api/v1/transacoes?orcamento=fora&mes={hoje.month}&ano={hoje.year}",
        headers=headers,
    )
    assert response_fora.status_code == 200
    ids_fora = {item["id"] for item in response_fora.json()}
    assert fora_1["id"] in ids_fora
    assert fora_2["id"] in ids_fora

    response_dentro = client.get(
        f"/api/v1/transacoes?orcamento=dentro&mes={hoje.month}&ano={hoje.year}",
        headers=headers,
    )
    assert response_dentro.status_code == 200
    items_dentro = response_dentro.json()
    assert any(item.get("categoria_id") == cat_dentro for item in items_dentro)
    assert all(item["tipo"] == "saida" for item in items_dentro)


def test_filtro_valor_ref_invalido_retorna_400(client):
    headers = _auth_headers(client)
    response = client.get("/api/v1/transacoes?valor_modo=gte&valor_ref=abc", headers=headers)
    assert response.status_code == 400
    assert "valor_ref invalido" in response.json()["detail"]
