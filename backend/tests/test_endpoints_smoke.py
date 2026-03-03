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


def test_categorias_requires_auth_and_returns_list(client):
    unauthorized = client.get("/api/v1/categorias")
    assert unauthorized.status_code == 401

    headers = _auth_headers(client)
    authorized = client.get("/api/v1/categorias", headers=headers)
    assert authorized.status_code == 200
    assert isinstance(authorized.json(), list)


def test_categorias_crud_usuario_e_bloqueio_padrao(client):
    headers = _auth_headers(client)

    create_response = client.post(
        "/api/v1/categorias",
        headers=headers,
        json={
            "nome": "Categoria Teste",
            "icone": "tag",
            "cor": "#123ABC",
            "tipo": "saida",
        },
    )
    assert create_response.status_code == 201
    categoria_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/categorias/{categoria_id}",
        headers=headers,
        json={"nome": "Categoria Editada"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["nome"] == "Categoria Editada"

    delete_response = client.delete(f"/api/v1/categorias/{categoria_id}", headers=headers)
    assert delete_response.status_code == 204

    outros_headers = _auth_headers(client)
    outro_create = client.post(
        "/api/v1/categorias",
        headers=outros_headers,
        json={
            "nome": "Categoria Outro Usuario",
            "icone": "tag",
            "cor": "#AA00CC",
            "tipo": "saida",
        },
    )
    assert outro_create.status_code == 201
    outro_id = outro_create.json()["id"]
    bloqueio_response = client.delete(f"/api/v1/categorias/{outro_id}", headers=headers)
    assert bloqueio_response.status_code == 404


def test_categoria_em_uso_nao_pode_excluir(client):
    headers = _auth_headers(client)

    categoria_response = client.post(
        "/api/v1/categorias",
        headers=headers,
        json={
            "nome": "Categoria Em Uso",
            "icone": "tag",
            "cor": "#111111",
            "tipo": "saida",
        },
    )
    assert categoria_response.status_code == 201
    categoria_id = categoria_response.json()["id"]

    conta_response = client.post(
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
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    transacao_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "categoria_id": categoria_id,
            "descricao": "Transacao usando categoria",
            "valor": 50.0,
            "tipo": "saida",
            "data": "2026-02-10",
            "status_liquidacao": "previsto",
        },
    )
    assert transacao_response.status_code == 201

    delete_response = client.delete(f"/api/v1/categorias/{categoria_id}", headers=headers)
    assert delete_response.status_code == 400
    assert "Categoria em uso" in delete_response.json()["detail"]


def test_metas_crud_smoke(client):
    headers = _auth_headers(client)
    hoje = date.today().isoformat()

    create_response = client.post(
        "/api/v1/metas",
        headers=headers,
        json={
            "nome": "Meta Smoke",
            "descricao": "Teste de endpoint",
            "valor_alvo": 1500.0,
            "valor_atual": 0.0,
            "data_inicio": hoje,
            "data_fim": hoje,
            "concluida": False,
            "cor": "#10B981",
        },
    )
    assert create_response.status_code == 201
    meta_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/metas/{meta_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["nome"] == "Meta Smoke"

    update_response = client.put(
        f"/api/v1/metas/{meta_id}",
        headers=headers,
        json={"valor_atual": 250.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["valor_atual"] == 250.0

    delete_response = client.delete(f"/api/v1/metas/{meta_id}", headers=headers)
    assert delete_response.status_code == 204


def test_orcamentos_crud_smoke(client):
    headers = _auth_headers(client)
    hoje = date.today()

    create_response = client.post(
        "/api/v1/orcamentos",
        headers=headers,
        json={
            "categoria_id": 999,
            "mes": hoje.month,
            "ano": hoje.year,
            "valor_planejado": 800.0,
        },
    )
    assert create_response.status_code == 201
    orcamento_id = create_response.json()["id"]

    get_response = client.get(f"/api/v1/orcamentos/{orcamento_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["valor_planejado"] == 800.0

    update_response = client.put(
        f"/api/v1/orcamentos/{orcamento_id}",
        headers=headers,
        json={"valor_planejado": 950.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["valor_planejado"] == 950.0

    delete_response = client.delete(f"/api/v1/orcamentos/{orcamento_id}", headers=headers)
    assert delete_response.status_code == 204


def test_orcamento_lista_recalcula_valor_gasto(client):
    headers = _auth_headers(client)
    hoje = date.today()
    data_iso = hoje.isoformat()

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Orcamento",
            "tipo": "conta_corrente",
            "saldo": 1000.0,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    categoria_id = 999
    transacao_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "categoria_id": categoria_id,
            "descricao": "Despesa para orcamento",
            "valor": 200.0,
            "valor_multa": 10.0,
            "valor_juros": 5.0,
            "valor_desconto": 5.0,
            "tipo": "saida",
            "data": data_iso,
            "status_liquidacao": "previsto",
        },
    )
    assert transacao_response.status_code == 201

    orcamento_response = client.post(
        "/api/v1/orcamentos",
        headers=headers,
        json={
            "categoria_id": categoria_id,
            "mes": hoje.month,
            "ano": hoje.year,
            "valor_planejado": 1000.0,
        },
    )
    assert orcamento_response.status_code == 201

    lista = client.get(
        f"/api/v1/orcamentos?mes={hoje.month}&ano={hoje.year}",
        headers=headers,
    )
    assert lista.status_code == 200
    assert len(lista.json()) >= 1
    assert lista.json()[0]["valor_gasto"] == 210.0
