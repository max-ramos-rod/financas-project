import uuid
from datetime import date, timedelta


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


def _criar_conta_cartao(client, headers):
    response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Cartao Teste",
            "tipo": "cartao_credito",
            "saldo": 0,
            "dia_fechamento": 20,
            "dia_vencimento": 28,
            "limite_credito": 5000,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _criar_conta_pagamento(client, headers, saldo: float = 5000.0):
    response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Corrente",
            "tipo": "conta_corrente",
            "saldo": saldo,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_fatura_atual_retorna_apenas_itens_em_aberto_no_periodo(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)

    fatura_inicial = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-atual", headers=headers)
    assert fatura_inicial.status_code == 200
    periodo_inicio = date.fromisoformat(fatura_inicial.json()["periodo_inicio"])
    periodo_fim = date.fromisoformat(fatura_inicial.json()["periodo_fim"])

    em_periodo = periodo_inicio.isoformat()
    fora_periodo = (periodo_inicio - timedelta(days=1)).isoformat()

    cria_1 = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra na fatura",
            "valor": 100.0,
            "valor_multa": 10.0,
            "valor_juros": 5.0,
            "valor_desconto": 2.0,
            "tipo": "saida",
            "data": em_periodo,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_1.status_code == 201

    cria_2 = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra fora periodo",
            "valor": 70.0,
            "tipo": "saida",
            "data": fora_periodo,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_2.status_code == 201

    fatura = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-atual", headers=headers)
    assert fatura.status_code == 200
    payload = fatura.json()

    assert payload["periodo_inicio"] == periodo_inicio.isoformat()
    assert payload["periodo_fim"] == periodo_fim.isoformat()
    assert payload["total_itens"] == 1
    assert payload["valor_total"] == 113.0
    assert payload["itens"][0]["descricao"] == "Compra na fatura"
    assert payload["itens"][0]["status_liquidacao"] in ("previsto", "atrasado")


def test_pagar_fatura_liquida_itens_e_debita_conta_pagamento(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)
    conta_pagamento_id = _criar_conta_pagamento(client, headers, saldo=2000.0)

    fatura_inicial = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-atual", headers=headers)
    assert fatura_inicial.status_code == 200
    data_item = fatura_inicial.json()["periodo_inicio"]

    cria_1 = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra A",
            "valor": 120.0,
            "tipo": "saida",
            "data": data_item,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_1.status_code == 201
    id_1 = cria_1.json()["id"]

    cria_2 = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra B",
            "valor": 80.0,
            "valor_juros": 10.0,
            "tipo": "saida",
            "data": data_item,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_2.status_code == 201
    id_2 = cria_2.json()["id"]

    pagamento_data = date.today().isoformat()
    pagar = client.post(
        f"/api/v1/contas/{conta_cartao_id}/pagar-fatura",
        headers=headers,
        json={
            "conta_pagamento_id": conta_pagamento_id,
            "data_pagamento": pagamento_data,
            "descricao": "Pagamento teste fatura",
        },
    )
    assert pagar.status_code == 200
    assert pagar.json()["total_itens"] == 0
    assert pagar.json()["valor_total"] == 0

    contas = client.get("/api/v1/contas", headers=headers)
    assert contas.status_code == 200
    conta_pagamento = next(c for c in contas.json() if c["id"] == conta_pagamento_id)
    assert conta_pagamento["saldo"] == 1790.0

    transacoes = client.get("/api/v1/transacoes", headers=headers)
    assert transacoes.status_code == 200
    lista = transacoes.json()

    item_1 = next(t for t in lista if t["id"] == id_1)
    item_2 = next(t for t in lista if t["id"] == id_2)
    assert item_1["status_liquidacao"] == "liquidado"
    assert item_2["status_liquidacao"] == "liquidado"
    assert item_1["data_liquidacao"] == pagamento_data
    assert item_2["data_liquidacao"] == pagamento_data

    transferencia = next(
        t for t in lista
        if t["tipo"] == "transferencia" and t["conta_id"] == conta_pagamento_id and t["descricao"] == "Pagamento teste fatura"
    )
    assert transferencia["valor"] == 210.0
    assert transferencia["status_liquidacao"] == "liquidado"
    assert transferencia["data_liquidacao"] == pagamento_data
