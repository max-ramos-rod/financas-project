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


def test_dre_mensal_retorna_resumo_pago_previsto(client):
    headers = _auth_headers(client)

    conta_response = client.post(
        "/api/v1/contas",
        headers=headers,
        json={
            "nome": "Conta DRE",
            "tipo": "conta_corrente",
            "saldo": 1000.0,
            "cor": "#10B981",
            "ativa": True,
        },
    )
    assert conta_response.status_code == 201
    conta_id = conta_response.json()["id"]

    hoje = date.today()
    mes = hoje.month
    ano = hoje.year
    data_iso = hoje.isoformat()

    cria_entrada_liq = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Entrada liquidada",
            "valor": 1000.0,
            "tipo": "entrada",
            "data": data_iso,
            "status_liquidacao": "liquidado",
            "data_liquidacao": data_iso,
        },
    )
    assert cria_entrada_liq.status_code == 201

    cria_entrada_prev = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Entrada prevista",
            "valor": 500.0,
            "tipo": "entrada",
            "data": data_iso,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_entrada_prev.status_code == 201

    cria_saida_liq = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Saida liquidada",
            "valor": 400.0,
            "tipo": "saida",
            "data": data_iso,
            "status_liquidacao": "liquidado",
            "data_liquidacao": data_iso,
        },
    )
    assert cria_saida_liq.status_code == 201

    cria_saida_prev = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Saida prevista",
            "valor": 300.0,
            "tipo": "saida",
            "data": data_iso,
            "status_liquidacao": "previsto",
        },
    )
    assert cria_saida_prev.status_code == 201

    dre = client.get(f"/api/v1/relatorios/dre-mensal?mes={mes}&ano={ano}", headers=headers)
    assert dre.status_code == 200
    payload = dre.json()

    assert payload["entradas_liquidadas"] == 1000.0
    assert payload["entradas_previstas"] == 500.0
    assert payload["entradas_total"] == 1500.0
    assert payload["saidas_liquidadas"] == 400.0
    assert payload["saidas_previstas"] == 300.0
    assert payload["saidas_total"] == 700.0
    assert payload["resultado_liquidado"] == 600.0
    assert payload["resultado_previsto"] == 200.0
    assert payload["resultado_total"] == 800.0


def test_dre_mensal_export_csv(client):
    headers = _auth_headers(client)
    hoje = date.today()
    mes = hoje.month
    ano = hoje.year

    response = client.get(f"/api/v1/relatorios/dre-mensal/export?mes={mes}&ano={ano}", headers=headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    content_disposition = response.headers.get("content-disposition", "")
    assert f'dre_mensal_{ano}_{mes:02d}.csv' in content_disposition
    assert "DRE Mensal" in response.text


def test_dre_mensal_export_pdf(client):
    headers = _auth_headers(client)
    hoje = date.today()
    mes = hoje.month
    ano = hoje.year

    response = client.get(f"/api/v1/relatorios/dre-mensal/export-pdf?mes={mes}&ano={ano}", headers=headers)
    assert response.status_code == 200
    assert "application/pdf" in response.headers.get("content-type", "")
    content_disposition = response.headers.get("content-disposition", "")
    assert f'dre_mensal_{ano}_{mes:02d}.pdf' in content_disposition
    assert response.content.startswith(b"%PDF-")
