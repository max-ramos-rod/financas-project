"""
Cobertura de casos negativos: 404 (recursos inexistentes), isolamento entre
usuários e validações 400/422 que não tinham teste dedicado.
"""
import uuid
from datetime import date

# ---------------------------------------------------------------------------
# Helpers compartilhados
# ---------------------------------------------------------------------------

def _register_and_login(client, email: str | None = None) -> dict:
    email = email or f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "senha123", "nome": "Teste", "role": "user"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "senha123"},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _criar_conta(client, headers) -> int:
    resp = client.post(
        "/api/v1/contas",
        headers=headers,
        json={"nome": "Conta Corrente", "tipo": "conta_corrente", "saldo": 1000.0, "cor": "#3B82F6", "ativa": True},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _criar_transacao(client, headers, conta_id: int) -> int:
    resp = client.post(
        "/api/v1/transacoes",
        headers=headers,
        json={
            "conta_id": conta_id,
            "descricao": "Transação Teste",
            "valor": 50.0,
            "tipo": "saida",
            "data": str(date.today()),
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _criar_meta(client, headers) -> int:
    resp = client.post(
        "/api/v1/metas",
        headers=headers,
        json={
            "nome": "Meta Teste",
            "valor_alvo": 500.0,
            "data_inicio": str(date.today()),
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _criar_orcamento(client, headers, categoria_id: int) -> int:
    resp = client.post(
        "/api/v1/orcamentos",
        headers=headers,
        json={
            "categoria_id": categoria_id,
            "mes": date.today().month,
            "ano": date.today().year,
            "valor_planejado": 300.0,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _criar_categoria_saida(client, headers) -> int:
    resp = client.post(
        "/api/v1/categorias",
        headers=headers,
        json={"nome": f"Cat_{uuid.uuid4().hex[:6]}", "icone": "tag", "cor": "#10B981", "tipo": "saida"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ===========================================================================
# Grupo 1 — 404: recursos inexistentes
# ===========================================================================

ID_INEXISTENTE = 999_999


def test_transacao_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/transacoes/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_editar_transacao_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.put(
        f"/api/v1/transacoes/{ID_INEXISTENTE}",
        headers=h,
        json={"descricao": "Nova desc"},
    )
    assert r.status_code == 404


def test_excluir_transacao_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.delete(f"/api/v1/transacoes/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_meta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/metas/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_editar_meta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.put(f"/api/v1/metas/{ID_INEXISTENTE}", headers=h, json={"nome": "X"})
    assert r.status_code == 404


def test_excluir_meta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.delete(f"/api/v1/metas/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_orcamento_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/orcamentos/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_editar_orcamento_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.put(
        f"/api/v1/orcamentos/{ID_INEXISTENTE}",
        headers=h,
        json={"valor_planejado": 100.0},
    )
    assert r.status_code == 404


def test_excluir_orcamento_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.delete(f"/api/v1/orcamentos/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_conta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/contas/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_editar_conta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.put(
        f"/api/v1/contas/{ID_INEXISTENTE}",
        headers=h,
        json={"nome": "X", "cor": "#000000"},
    )
    assert r.status_code == 404


def test_excluir_conta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.delete(f"/api/v1/contas/{ID_INEXISTENTE}", headers=h)
    assert r.status_code == 404


def test_fatura_de_conta_inexistente_retorna_404(client):
    h = _register_and_login(client)
    r = client.get(f"/api/v1/contas/{ID_INEXISTENTE}/fatura-atual", headers=h)
    assert r.status_code == 404


def test_fatura_de_conta_corrente_retorna_400(client):
    """Fatura só existe em cartão de crédito; pedir em conta corrente é 400."""
    h = _register_and_login(client)
    conta_id = _criar_conta(client, h)
    r = client.get(f"/api/v1/contas/{conta_id}/fatura-atual", headers=h)
    assert r.status_code == 400


# ===========================================================================
# Grupo 2 — Isolamento entre usuários (cross-user → 404)
# ===========================================================================

def test_usuario_nao_ve_transacao_de_outro_usuario(client):
    h_a = _register_and_login(client)
    conta_a = _criar_conta(client, h_a)
    transacao_a = _criar_transacao(client, h_a, conta_a)

    h_b = _register_and_login(client)
    r = client.get(f"/api/v1/transacoes/{transacao_a}", headers=h_b)
    assert r.status_code == 404


def test_usuario_nao_edita_transacao_de_outro_usuario(client):
    h_a = _register_and_login(client)
    conta_a = _criar_conta(client, h_a)
    transacao_a = _criar_transacao(client, h_a, conta_a)

    h_b = _register_and_login(client)
    r = client.put(
        f"/api/v1/transacoes/{transacao_a}",
        headers=h_b,
        json={"descricao": "Tentativa de edição"},
    )
    assert r.status_code == 404


def test_usuario_nao_deleta_transacao_de_outro_usuario(client):
    h_a = _register_and_login(client)
    conta_a = _criar_conta(client, h_a)
    transacao_a = _criar_transacao(client, h_a, conta_a)

    h_b = _register_and_login(client)
    r = client.delete(f"/api/v1/transacoes/{transacao_a}", headers=h_b)
    assert r.status_code == 404


def test_usuario_nao_ve_conta_de_outro_usuario(client):
    h_a = _register_and_login(client)
    conta_a = _criar_conta(client, h_a)

    h_b = _register_and_login(client)
    r = client.get(f"/api/v1/contas/{conta_a}", headers=h_b)
    assert r.status_code == 404


def test_usuario_nao_ve_meta_de_outro_usuario(client):
    h_a = _register_and_login(client)
    meta_a = _criar_meta(client, h_a)

    h_b = _register_and_login(client)
    r = client.get(f"/api/v1/metas/{meta_a}", headers=h_b)
    assert r.status_code == 404


def test_usuario_nao_ve_orcamento_de_outro_usuario(client):
    h_a = _register_and_login(client)
    cat_id = _criar_categoria_saida(client, h_a)
    orcamento_a = _criar_orcamento(client, h_a, cat_id)

    h_b = _register_and_login(client)
    r = client.get(f"/api/v1/orcamentos/{orcamento_a}", headers=h_b)
    assert r.status_code == 404


# ===========================================================================
# Grupo 3 — 422: Validações de schema (Pydantic)
# ===========================================================================

def test_transacao_com_valor_zero_retorna_422(client):
    h = _register_and_login(client)
    conta_id = _criar_conta(client, h)
    r = client.post(
        "/api/v1/transacoes",
        headers=h,
        json={
            "conta_id": conta_id,
            "descricao": "Valor zero",
            "valor": 0,
            "tipo": "saida",
            "data": str(date.today()),
        },
    )
    assert r.status_code == 422


def test_transacao_com_valor_negativo_retorna_422(client):
    h = _register_and_login(client)
    conta_id = _criar_conta(client, h)
    r = client.post(
        "/api/v1/transacoes",
        headers=h,
        json={
            "conta_id": conta_id,
            "descricao": "Valor negativo",
            "valor": -10.0,
            "tipo": "saida",
            "data": str(date.today()),
        },
    )
    assert r.status_code == 422


def test_transacao_parcelada_sem_total_parcelas_retorna_422(client):
    h = _register_and_login(client)
    conta_id = _criar_conta(client, h)
    r = client.post(
        "/api/v1/transacoes",
        headers=h,
        json={
            "conta_id": conta_id,
            "descricao": "Parcelado inválido",
            "valor": 100.0,
            "tipo": "saida",
            "data": str(date.today()),
            "parcelado": True,
            "total_parcelas": 1,
        },
    )
    assert r.status_code == 422


def test_transacao_total_parcelas_acima_do_limite_retorna_422(client):
    h = _register_and_login(client)
    conta_id = _criar_conta(client, h)
    r = client.post(
        "/api/v1/transacoes",
        headers=h,
        json={
            "conta_id": conta_id,
            "descricao": "Parcelas demais",
            "valor": 100.0,
            "tipo": "saida",
            "data": str(date.today()),
            "parcelado": True,
            "total_parcelas": 49,
        },
    )
    assert r.status_code == 422


def test_transacao_sem_descricao_retorna_422(client):
    h = _register_and_login(client)
    conta_id = _criar_conta(client, h)
    r = client.post(
        "/api/v1/transacoes",
        headers=h,
        json={
            "conta_id": conta_id,
            "descricao": "",
            "valor": 50.0,
            "tipo": "saida",
            "data": str(date.today()),
        },
    )
    assert r.status_code == 422


def test_meta_sem_nome_retorna_422(client):
    h = _register_and_login(client)
    r = client.post(
        "/api/v1/metas",
        headers=h,
        json={"valor_alvo": 500.0, "data_inicio": str(date.today())},
    )
    assert r.status_code == 422


def test_meta_sem_valor_alvo_retorna_422(client):
    h = _register_and_login(client)
    r = client.post(
        "/api/v1/metas",
        headers=h,
        json={"nome": "Meta sem alvo", "data_inicio": str(date.today())},
    )
    assert r.status_code == 422
