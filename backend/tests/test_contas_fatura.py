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


def _criar_conta_cartao_custom(client, headers, nome: str, dia_fechamento: int, dia_vencimento: int):
    response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": nome,
            "tipo": "cartao_credito",
            "saldo": 0,
            "dia_fechamento": dia_fechamento,
            "dia_vencimento": dia_vencimento,
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

    fatura_fechada = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-fechada", headers=headers)
    assert fatura_fechada.status_code == 200
    data_item = fatura_fechada.json()["periodo_inicio"]

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
    assert pagar.json()["total_itens"] == 2
    assert pagar.json()["valor_total"] == 210.0
    assert pagar.json()["valor_pago"] == 210.0
    assert pagar.json()["valor_a_pagar"] == 0

    contas = client.get("/api/v1/contas", headers=headers)
    assert contas.status_code == 200
    conta_pagamento = next(c for c in contas.json() if c["id"] == conta_pagamento_id)
    assert conta_pagamento["saldo"] == 1790.0
    cartao = next(c for c in contas.json() if c["id"] == conta_cartao_id)
    assert cartao["valor_fatura_fechada"] == 0
    assert cartao["valor_fatura_fechada_pago"] == 210.0
    assert cartao["valor_fatura_fechada_total"] == 210.0

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


def test_listar_contas_retorna_resumo_fatura_aberta_por_cartao(client):
    headers = _auth_headers(client)
    cartao_a_id = _criar_conta_cartao_custom(client, headers, "Cartao A", 20, 28)
    cartao_b_id = _criar_conta_cartao_custom(client, headers, "Cartao B", 10, 18)

    fatura_a = client.get(f"/api/v1/contas/{cartao_a_id}/fatura-atual", headers=headers)
    fatura_b = client.get(f"/api/v1/contas/{cartao_b_id}/fatura-atual", headers=headers)
    assert fatura_a.status_code == 200
    assert fatura_b.status_code == 200

    data_a = fatura_a.json()["periodo_inicio"]
    data_b = fatura_b.json()["periodo_inicio"]

    cria_a = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": cartao_a_id,
            "descricao": "Compra cartao A",
            "valor": 150.0,
            "tipo": "saida",
            "data": data_a,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_a.status_code == 201

    cria_b = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": cartao_b_id,
            "descricao": "Compra cartao B",
            "valor": 300.0,
            "valor_juros": 20.0,
            "tipo": "saida",
            "data": data_b,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_b.status_code == 201

    contas = client.get("/api/v1/contas", headers=headers)
    assert contas.status_code == 200

    cartao_a = next(c for c in contas.json() if c["id"] == cartao_a_id)
    cartao_b = next(c for c in contas.json() if c["id"] == cartao_b_id)

    assert cartao_a["valor_fatura_aberta"] == 150.0
    assert cartao_a["valor_fatura_fechada_total"] == 0
    assert cartao_a["valor_fatura_fechada_pago"] == 0
    assert cartao_a["total_itens_fatura_aberta"] == 1
    assert cartao_a["periodo_fatura_inicio"] == fatura_a.json()["periodo_inicio"]
    assert cartao_a["periodo_fatura_fim"] == fatura_a.json()["periodo_fim"]
    assert cartao_a["valor_fatura_fechada"] == 0
    assert cartao_a["total_itens_fatura_fechada"] == 0

    assert cartao_b["valor_fatura_aberta"] == 320.0
    assert cartao_b["valor_fatura_fechada_total"] == 0
    assert cartao_b["valor_fatura_fechada_pago"] == 0
    assert cartao_b["total_itens_fatura_aberta"] == 1
    assert cartao_b["periodo_fatura_inicio"] == fatura_b.json()["periodo_inicio"]
    assert cartao_b["periodo_fatura_fim"] == fatura_b.json()["periodo_fim"]
    assert cartao_b["valor_fatura_fechada"] == 0
    assert cartao_b["total_itens_fatura_fechada"] == 0


def test_fatura_fechada_retorna_ciclo_anterior_ao_aberto(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)

    fatura_fechada = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-fechada", headers=headers)
    fatura_aberta = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-atual", headers=headers)

    assert fatura_fechada.status_code == 200
    assert fatura_aberta.status_code == 200

    payload_fechada = fatura_fechada.json()
    payload_aberta = fatura_aberta.json()

    assert payload_fechada["periodo_fim"] < payload_aberta["periodo_inicio"]
    assert payload_fechada["data_vencimento_fatura"] <= payload_aberta["data_vencimento_fatura"]


def test_pagamento_sem_descricao_usa_prefixo_ftpg(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)
    conta_pagamento_id = _criar_conta_pagamento(client, headers, saldo=1000.0)

    fatura_fechada = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-fechada", headers=headers)
    assert fatura_fechada.status_code == 200

    cria = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra default descricao",
            "valor": 50.0,
            "tipo": "saida",
            "data": fatura_fechada.json()["periodo_inicio"],
            "status_liquidacao": "previsto",
        },
    )
    assert cria.status_code == 201

    pagar = client.post(
        f"/api/v1/contas/{conta_cartao_id}/pagar-fatura",
        headers=headers,
        json={"conta_pagamento_id": conta_pagamento_id},
    )
    assert pagar.status_code == 200

    transacoes = client.get("/api/v1/transacoes", headers=headers)
    assert transacoes.status_code == 200
    transferencia = next(
        t for t in transacoes.json()
        if t["tipo"] == "transferencia" and t["conta_id"] == conta_pagamento_id
    )
    assert transferencia["descricao"].startswith("FTPG Cartao Teste")


def test_ajustar_ciclo_fatura_atual_aplica_datas_reais_e_observacao(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)

    fatura_inicial = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-atual", headers=headers)
    assert fatura_inicial.status_code == 200
    payload_inicial = fatura_inicial.json()

    ajuste = client.put(
        f"/api/v1/contas/{conta_cartao_id}/fatura-atual/ajuste-ciclo",
        headers=headers,
        json={
            "data_fechamento_real": "2026-04-22",
            "data_vencimento_real": "2026-04-30",
            "observacao": "Postergado por feriado bancario.",
        },
    )
    assert ajuste.status_code == 200
    payload = ajuste.json()

    assert payload["competencia_ano"] == payload_inicial["competencia_ano"]
    assert payload["competencia_mes"] == payload_inicial["competencia_mes"]
    assert payload["data_fechamento_prevista"] == payload_inicial["data_fechamento_prevista"]
    assert payload["data_fechamento_real"] == "2026-04-22"
    assert payload["data_fechamento_fatura"] == "2026-04-22"
    assert payload["data_vencimento_prevista"] == payload_inicial["data_vencimento_prevista"]
    assert payload["data_vencimento_fatura"] == "2026-04-30"
    assert payload["observacao_ciclo"] == "Postergado por feriado bancario."

    contas = client.get("/api/v1/contas", headers=headers)
    assert contas.status_code == 200
    cartao = next(c for c in contas.json() if c["id"] == conta_cartao_id)
    assert cartao["data_fechamento_fatura"] == "2026-04-22"
    assert cartao["data_vencimento_fatura"] == "2026-04-30"


def test_limpar_ajuste_ciclo_fatura_atual_retorna_para_datas_previstas(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)

    ajuste = client.put(
        f"/api/v1/contas/{conta_cartao_id}/fatura-atual/ajuste-ciclo",
        headers=headers,
        json={
            "data_fechamento_real": "2026-04-22",
            "data_vencimento_real": "2026-04-30",
            "observacao": "Excecao do mes.",
        },
    )
    assert ajuste.status_code == 200

    limpar = client.delete(f"/api/v1/contas/{conta_cartao_id}/fatura-atual/ajuste-ciclo", headers=headers)
    assert limpar.status_code == 200
    payload = limpar.json()

    assert payload["data_fechamento_real"] is None
    assert payload["observacao_ciclo"] is None
    assert payload["data_fechamento_fatura"] == payload["data_fechamento_prevista"]
    assert payload["data_vencimento_fatura"] == payload["data_vencimento_prevista"]


def test_ajuste_de_fechamento_real_inclui_compras_nos_dias_extras_do_ciclo(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)

    fora_do_padrao = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra no dia extra do ciclo",
            "valor": 99.0,
            "tipo": "saida",
            "data": "2026-04-21",
            "status_liquidacao": "previsto",
        },
    )
    assert fora_do_padrao.status_code == 201

    antes_ajuste = client.get(f"/api/v1/contas/{conta_cartao_id}/fatura-atual", headers=headers)
    assert antes_ajuste.status_code == 200
    descricoes_antes = [item["descricao"] for item in antes_ajuste.json()["itens"]]
    assert "Compra no dia extra do ciclo" not in descricoes_antes

    ajuste = client.put(
        f"/api/v1/contas/{conta_cartao_id}/fatura-atual/ajuste-ciclo",
        headers=headers,
        json={
            "data_fechamento_real": "2026-04-22",
            "observacao": "Fechamento atrasou por feriado.",
        },
    )
    assert ajuste.status_code == 200
    descricoes_depois = [item["descricao"] for item in ajuste.json()["itens"]]
    assert "Compra no dia extra do ciclo" in descricoes_depois


def test_ajustar_ciclo_antigo_por_competencia(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)

    compra_dia_extra = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra ciclo antigo ajustado",
            "valor": 125.0,
            "tipo": "saida",
            "data": "2026-03-21",
            "status_liquidacao": "previsto",
        },
    )
    assert compra_dia_extra.status_code == 201

    antes = client.get(f"/api/v1/contas/{conta_cartao_id}/faturas/2026/3", headers=headers)
    assert antes.status_code == 200
    assert "Compra ciclo antigo ajustado" not in [item["descricao"] for item in antes.json()["itens"]]

    ajuste = client.put(
        f"/api/v1/contas/{conta_cartao_id}/faturas/2026/3/ajuste-ciclo",
        headers=headers,
        json={
            "data_fechamento_real": "2026-03-22",
            "data_vencimento_real": "2026-04-01",
            "observacao": "Ajuste manual de fatura antiga.",
        },
    )
    assert ajuste.status_code == 200
    payload = ajuste.json()

    assert payload["competencia_ano"] == 2026
    assert payload["competencia_mes"] == 3
    assert payload["data_fechamento_real"] == "2026-03-22"
    assert payload["data_fechamento_fatura"] == "2026-03-22"
    assert payload["data_vencimento_real"] == "2026-04-01"
    assert payload["data_vencimento_fatura"] == "2026-04-01"
    assert payload["observacao_ciclo"] == "Ajuste manual de fatura antiga."
    assert "Compra ciclo antigo ajustado" in [item["descricao"] for item in payload["itens"]]


def test_pagar_fatura_antiga_por_competencia(client):
    headers = _auth_headers(client)
    conta_cartao_id = _criar_conta_cartao(client, headers)
    conta_pagamento_id = _criar_conta_pagamento(client, headers, saldo=1000.0)

    compra = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_cartao_id,
            "descricao": "Compra fatura antiga",
            "valor": 200.0,
            "tipo": "saida",
            "data": "2026-03-10",
            "status_liquidacao": "previsto",
        },
    )
    assert compra.status_code == 201
    transacao_id = compra.json()["id"]

    pagar = client.post(
        f"/api/v1/contas/{conta_cartao_id}/faturas/2026/3/pagar",
        headers=headers,
        json={
            "conta_pagamento_id": conta_pagamento_id,
            "data_pagamento": "2026-04-01",
        },
    )
    assert pagar.status_code == 200
    assert pagar.json()["valor_total"] == 200.0
    assert pagar.json()["valor_pago"] == 200.0
    assert pagar.json()["valor_a_pagar"] == 0

    transacoes = client.get("/api/v1/transacoes", headers=headers)
    assert transacoes.status_code == 200
    item = next(t for t in transacoes.json() if t["id"] == transacao_id)
    assert item["status_liquidacao"] == "liquidado"
    assert item["data_liquidacao"] == "2026-04-01"
