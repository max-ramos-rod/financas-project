# Backend — Guia de Testes

## Pré-requisitos

- Ambiente virtual criado em `backend/venv`
- Dependências instaladas com `pip install -r requirements.txt`

A suite usa banco SQLite em memória via `tests/conftest.py` — não requer PostgreSQL rodando.

## Executar

```bash
# Suite completa
cd backend
.\venv\Scripts\python.exe -m pytest -q

# Arquivo específico
.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py

# Verbose (ver nome de cada teste)
.\venv\Scripts\python.exe -m pytest -v
```

Warnings de bibliotecas de terceiros podem aparecer e não impedem o sucesso.

## Escopo por arquivo

### `test_auth.py`
- Registro de novo usuário
- Login retorna token JWT válido
- Refresh de sessão antes da expiração
- `GET /auth/me` retorna usuário autenticado
- Endpoint protegido rejeita request sem token

### `test_contas_cartao.py`
- Criação de conta cartão exige `dia_fechamento` e `dia_vencimento`
- `dia_fechamento == dia_vencimento` é rejeitado (backend e crud)
- Saldo forçado para zero no create/update de cartão de crédito
- Update de cartão valida igualdade dos dias ao atualizar parcialmente

### `test_contas_fatura.py`
- `GET /api/v1/contas/{id}/fatura-atual` — fatura do ciclo vigente
- `GET /api/v1/contas/{id}/fatura-fechada` — fatura do ciclo fechado
- `POST /api/v1/contas/{id}/pagar-fatura` — pagamento da fatura
- Ajuste de ciclo com data real de fechamento/vencimento
- Testes usam datas relativas ao mês atual (não quebram com o tempo)

### `test_cartao_fatura_ciclo.py`
- Cálculo de ciclos de fechamento e vencimento em múltiplos cenários
- Competência da fatura com dia de fechamento no início, meio e fim do mês
- Transações em diferentes posições do ciclo vão para a competência correta

### `test_endpoints_smoke.py`
- CRUD básico de categorias, metas e orçamentos
- Categoria em uso por uma transação não pode ser excluída

### `test_relatorios_dre.py`
- `GET /api/v1/relatorios/dre-mensal` — estrutura do DRE mensal
- Receitas, despesas e resultado por categoria

### `test_transacoes_cartao_meta_orcamento.py`
- Regras de transações com cartão de crédito (entrada bloqueada, saldo não altera)
- Atualização automática de meta ao lançar transação vinculada
- Atualização de orçamento ao criar/editar transação da categoria
- Dízimo automático: ligar e desligar na edição de transação existente

### `test_transacoes_filtros.py`
- Filtros de listagem: tipo, status, conta, categoria, valor (igual/gte/lte), período, busca textual
- Combinação de múltiplos filtros simultâneos
- Endpoint `/visao-financeira` com itens de fatura misturados a transações normais
