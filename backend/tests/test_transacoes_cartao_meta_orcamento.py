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


def test_transacao_cartao_entrada_permitida(client):
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
            "descricao": "Estorno no cartao",
            "valor": 100.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "status_liquidacao": "previsto",
        },
    )

    assert transacao_response.status_code == 201
    assert transacao_response.json()["tipo"] == "entrada"


def test_atualizar_transacao_entrada_para_cartao_permitida(client):
    headers = _auth_headers(client)

    conta_corrente_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Corrente",
            "tipo": "conta_corrente",
            "saldo": 500.0,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert conta_corrente_response.status_code == 201
    conta_corrente_id = conta_corrente_response.json()["id"]

    cartao_response = client.post(
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
    assert cartao_response.status_code == 201
    cartao_id = cartao_response.json()["id"]

    create_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_corrente_id,
            "descricao": "Recebimento inicial",
            "valor": 200.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "status_liquidacao": "liquidado",
            "data_liquidacao": date.today().isoformat(),
        },
    )
    assert create_response.status_code == 201
    transacao_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/transacoes/{transacao_id}",
        headers=headers,
        json={"conta_id": cartao_id},
    )

    assert update_response.status_code == 200
    assert update_response.json()["tipo"] == "entrada"


def test_transacao_entrada_em_conta_investimento_permitida(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Investimento Teste",
            "tipo": "investimento",
            "saldo": 0,
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
            "descricao": "Aporte",
            "valor": 100.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "status_liquidacao": "liquidado",
            "data_liquidacao": date.today().isoformat(),
        },
    )

    assert transacao_response.status_code == 201
    assert transacao_response.json()["tipo"] == "entrada"


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
    transacoes = lista.json()["data"]
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
    transacoes = lista.json()["data"]
    dizimos_da_entrada = [
        t for t in transacoes
        if t.get("e_dizimo") is True and t.get("entrada_origem_id") == transacao_id
    ]
    assert len(dizimos_da_entrada) == 1
    assert dizimos_da_entrada[0]["valor"] == 50.0


def test_editar_entrada_desligando_dizimo_remove_saida(client):
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
            "descricao": "Receita com dizimo",
            "valor": 700.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "tem_dizimo": True,
            "percentual_dizimo": 10.0,
        },
    )
    assert create_response.status_code == 201
    transacao_id = create_response.json()["id"]

    lista_antes = client.get("/api/v1/transacoes", headers=headers)
    assert lista_antes.status_code == 200
    dizimos_antes = [
        t for t in lista_antes.json()["data"]
        if t.get("e_dizimo") is True and t.get("entrada_origem_id") == transacao_id
    ]
    assert len(dizimos_antes) == 1

    update_response = client.put(
        f"/api/v1/transacoes/{transacao_id}",
        headers=headers,
        json={
            "tem_dizimo": False,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["tem_dizimo"] is False

    lista_depois = client.get("/api/v1/transacoes", headers=headers)
    assert lista_depois.status_code == 200
    dizimos_depois = [
        t for t in lista_depois.json()["data"]
        if t.get("e_dizimo") is True and t.get("entrada_origem_id") == transacao_id
    ]
    assert len(dizimos_depois) == 0


def test_duplicar_transacao_copia_dados_com_datas_atuais_e_status_previsto(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Duplicacao",
            "tipo": "conta_corrente",
            "saldo": 1000.0,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    original_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Despesa para duplicar",
            "valor": 123.45,
            "tipo": "saida",
            "data": "2026-03-10",
            "data_vencimento": "2026-03-15",
            "status_liquidacao": "liquidado",
            "data_liquidacao": "2026-03-15",
            "fixa": True,
            "recorrente": True,
            "observacoes": "Observacao original",
            "tags": "mensal",
            "valor_multa": 2.0,
            "valor_juros": 3.0,
            "valor_desconto": 1.0,
        },
    )
    assert original_response.status_code == 201
    original = original_response.json()

    duplicada_response = client.post(
        f"/api/v1/transacoes/{original['id']}/duplicar",
        headers=headers,
    )
    assert duplicada_response.status_code == 201
    duplicada = duplicada_response.json()
    hoje = date.today().isoformat()

    assert duplicada["id"] != original["id"]
    assert duplicada["transacao_uuid"] != original["transacao_uuid"]
    assert duplicada["conta_id"] == original["conta_id"]
    assert duplicada["descricao"] == original["descricao"]
    assert duplicada["valor"] == original["valor"]
    assert duplicada["tipo"] == original["tipo"]
    assert duplicada["data"] == hoje
    assert duplicada["data_vencimento"] == hoje
    assert duplicada["data_liquidacao"] is None
    assert duplicada["status_liquidacao"] == "previsto"
    assert duplicada["fixa"] is True
    assert duplicada["recorrente"] is True
    assert duplicada["observacoes"] == "Observacao original"
    assert duplicada["tags"] == "mensal"
    assert duplicada["valor_multa"] == 2.0
    assert duplicada["valor_juros"] == 3.0
    assert duplicada["valor_desconto"] == 1.0

    contas = client.get("/api/v1/contas", headers=headers)
    assert contas.status_code == 200
    conta = next(c for c in contas.json()["data"] if c["id"] == conta_id)
    assert conta["saldo"] == 872.55


def test_duplicar_transacao_de_dizimo_direto_bloqueia(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Dizimo",
            "tipo": "conta_corrente",
            "saldo": 0.0,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    entrada_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Receita com dizimo para duplicar",
            "valor": 1000.0,
            "tipo": "entrada",
            "data": date.today().isoformat(),
            "tem_dizimo": True,
            "percentual_dizimo": 10.0,
        },
    )
    assert entrada_response.status_code == 201

    lista = client.get("/api/v1/transacoes", headers=headers)
    assert lista.status_code == 200
    dizimo = next(t for t in lista.json()["data"] if t.get("e_dizimo") is True)

    duplicar_response = client.post(
        f"/api/v1/transacoes/{dizimo['id']}/duplicar",
        headers=headers,
    )
    assert duplicar_response.status_code == 400
    assert "dizimo" in duplicar_response.json()["detail"].lower()


def test_visao_financeira_consolida_lancamentos_de_cartao_em_fatura(client):
    headers = _auth_headers(client)

    conta_corrente_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta Corrente",
            "tipo": "conta_corrente",
            "saldo": 1000.0,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert conta_corrente_response.status_code == 201
    conta_corrente_id = conta_corrente_response.json()["id"]

    cartao_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Cartao Visa",
            "tipo": "cartao_credito",
            "saldo": 0,
            "dia_fechamento": 20,
            "dia_vencimento": 28,
            "limite_credito": 3000,
            "cor": "#3B82F6",
            "ativa": True,
        },
    )
    assert cartao_response.status_code == 201
    cartao_id = cartao_response.json()["id"]

    compra_cartao_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": cartao_id,
            "descricao": "Compra Cartao",
            "valor": 200.0,
            "tipo": "saida",
            "data": "2026-03-10",
            "status_liquidacao": "previsto",
        },
    )
    assert compra_cartao_response.status_code == 201

    despesa_normal_response = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_corrente_id,
            "descricao": "Despesa Normal",
            "valor": 50.0,
            "tipo": "saida",
            "data": "2026-03-05",
            "status_liquidacao": "previsto",
        },
    )
    assert despesa_normal_response.status_code == 201

    response = client.get(
        "/api/v1/transacoes/visao-financeira?mes=3&ano=2026",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    descricoes = [item["descricao"] for item in payload]

    assert "Compra Cartao" not in descricoes
    assert "Despesa Normal" in descricoes

    fatura = next(item for item in payload if item["item_tipo"] == "fatura_cartao")
    assert fatura["descricao"] == "Fatura Cartao Visa"
    assert fatura["conta_id"] == cartao_id
    assert fatura["valor"] == 200.0
    assert fatura["tipo"] == "saida"
    assert fatura["status_liquidacao"] == "previsto"
    assert fatura["data_vencimento"] == "2026-03-28"
    assert fatura["fatura_conta_id"] == cartao_id
    assert fatura["fatura_competencia_ano"] == 2026
    assert fatura["fatura_competencia_mes"] == 3
    assert fatura["fatura_total_itens"] == 1
