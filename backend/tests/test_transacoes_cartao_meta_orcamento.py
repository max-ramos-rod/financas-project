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


def test_transacao_cartao_saida_forca_status_previsto(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Cartao Teste",
            "tipo": "cartao_credito",
            "saldo": 0,
            "dia_fechamento": 20,
            "dia_vencimento": 28,
            "limite_credito": 3000,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    transacao_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Compra mercado",
            "valor": 150.0,
            "tipo": "saida",
            "data": "2026-02-16",
            "status_liquidacao": "liquidado",
            "data_liquidacao": "2026-02-16",
            "parcelado": False,
        },
    )

    assert transacao_response.status_code == 201
    payload = transacao_response.json()
    assert payload["status_liquidacao"] == "previsto"
    assert payload["data_liquidacao"] is None


def test_transacao_atualiza_meta_e_orcamento(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Corrente Teste",
            "tipo": "conta_corrente",
            "saldo": 1000.0,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    hoje = date.today()
    data_iso = hoje.isoformat()

    meta_response = client.post(
        "/api/v1/metas",
        headers=headers,
        json={
            "nome": "Meta mercado",
            "descricao": "Controlar gastos",
            "valor_alvo": 1000.0,
            "valor_atual": 0.0,
            "data_inicio": data_iso,
            "data_fim": data_iso,
            "concluida": False,
            "cor": "#10B981",
        },
    )
    assert meta_response.status_code == 201
    meta_id = meta_response.json()["id"]

    categoria_id = 999
    orcamento_response = client.post(
        "/api/v1/orcamentos",
        headers=headers,
        json={
            "categoria_id": categoria_id,
            "mes": hoje.month,
            "ano": hoje.year,
            "valor_planejado": 2000.0,
        },
    )
    assert orcamento_response.status_code == 201
    orcamento_id = orcamento_response.json()["id"]

    transacao_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "categoria_id": categoria_id,
            "descricao": "Mercado semana",
            "valor": 250.0,
            "tipo": "saida",
            "data": data_iso,
            "status_liquidacao": "previsto",
            "meta_id": meta_id,
            "parcelado": False,
        },
    )
    assert transacao_response.status_code == 201

    meta_get = client.get(f"/api/v1/metas/{meta_id}", headers=headers)
    assert meta_get.status_code == 200
    assert meta_get.json()["valor_atual"] == -250.0

    orcamento_get = client.get(f"/api/v1/orcamentos/{orcamento_id}", headers=headers)
    assert orcamento_get.status_code == 200
    assert orcamento_get.json()["valor_gasto"] == 250.0


def test_dizimo_automatico_gera_categoria_dizimo(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Entrada",
            "tipo": "conta_corrente",
            "saldo": 0.0,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    transacao_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Recebimento",
            "valor": 1000.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "tem_dizimo": True,
            "percentual_dizimo": 10.0,
        },
    )
    assert transacao_response.status_code == 201

    lista = client.get("/api/v1/transacoes", headers=headers)
    assert lista.status_code == 200
    transacoes = lista.json()
    dizimos = [t for t in transacoes if t.get("e_dizimo") is True]
    assert len(dizimos) >= 1
    assert all(t.get("categoria_id") is not None for t in dizimos)


def test_editar_entrada_ativando_dizimo_cria_saida(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Principal",
            "tipo": "conta_corrente",
            "saldo": 0.0,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    create_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Receita sem dizimo",
            "valor": 500.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "tem_dizimo": False,
        },
    )
    assert create_response.status_code == 201
    transacao_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/transacoes/{transacao_id}",
        headers=headers,
        json={
            "tem_dizimo": True,
            "percentual_dizimo": 10.0,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["tem_dizimo"] is True

    lista = client.get("/api/v1/transacoes", headers=headers)
    assert lista.status_code == 200
    transacoes = lista.json()
    dizimos_da_entrada = [
        t for t in transacoes
        if t.get("e_dizimo") is True and t.get("entrada_origem_id") == transacao_id
    ]
    assert len(dizimos_da_entrada) == 1
    assert dizimos_da_entrada[0]["valor"] == 50.0
