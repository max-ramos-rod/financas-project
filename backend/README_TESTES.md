# Backend — Guia de Testes

## Pré-requisitos

- Ambiente virtual criado em `backend/venv`
- Dependências instaladas com `pip install -r requirements.txt`

A suite de integração usa banco SQLite em memória via `tests/conftest.py` — não requer PostgreSQL rodando.
A suite unitária (`tests/unit/`) usa fakes de repository e não toca banco nenhum.

## Executar

```bash
# Suite completa
cd backend
.\venv\Scripts\python.exe -m pytest -q

# Arquivo específico
.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py

# Somente testes unitários
.\venv\Scripts\python.exe -m pytest -q tests/unit/

# Verbose (ver nome de cada teste)
.\venv\Scripts\python.exe -m pytest -v
```

Warnings de bibliotecas de terceiros podem aparecer e não impedem o sucesso.

## Escopo por arquivo — Integração (`tests/`)

### `test_auth.py`
- Registro de novo usuário
- Login retorna token JWT válido
- Refresh de sessão antes da expiração
- `GET /auth/me` retorna usuário autenticado
- Endpoint protegido rejeita request sem token

### `test_auth_password_reset.py`
- `POST /auth/forgot-password` com e-mail existente → 200 + mensagem genérica
- `POST /auth/forgot-password` com e-mail inexistente → 200 + mesma mensagem (não revelar)
- `POST /auth/reset-password` com token válido → 200 + senha alterada
- Token expirado → 400
- Token já usado → 400
- Token inválido → 400
- Fluxo completo: forgot → reset → login com nova senha

### `test_auth_rate_limiting.py`
- 429 após exceder limite em `/auth/login`
- 429 após exceder limite em `/auth/forgot-password`
- Usa `client_with_limiter` (fixture especial com limiter habilitado — os demais testes usam `disable_rate_limiting` autouse)

### `test_busca.py`
- `GET /busca?q=<termo>` retorna transações e contas matching
- Busca respeita isolamento de usuário (não vaza dados de terceiros)
- `q` com menos de 2 caracteres retorna 422

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

### `test_negativos.py`
- Cenários de erro esperados: acesso a recursos de outro usuário, IDs inexistentes, operações inválidas
- Garante que o isolamento de dados entre usuários funciona corretamente

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

## Escopo por arquivo — Unitários (`tests/unit/`)

Os testes unitários não usam banco de dados — utilizam implementações `Fake*Repository` definidas em `tests/unit/conftest.py`.

### `tests/unit/conftest.py`
- `FakeTransacaoRepository`, `FakeContaRepository`, `FakeCategoriaRepository`, etc.
- `make_db(conta)` — mock de Session SQLAlchemy
- `make_transacao_create(...)`, `make_conta(...)` — factories de dados

### `test_domain_transacao.py`
- `impacto_no_saldo` — status previsto não altera, liquidado altera
- `normalizar_atraso` — transação prevista com vencimento passado vira "atrasado"
- `valor_meta` — cancelado = 0, entrada positivo, saída negativo

### `test_service_transacao.py`
- Criar transação simples: saída prevista não altera saldo, liquidada altera
- Parcelamento: criação de N parcelas com grupo_uuid compartilhado
- Dízimo: criação automática da transação de saída vinculada
- Validações: conta não encontrada, total_parcelas < 2, parcelado + recorrente

### `test_service_conta.py`
- Criar conta cartão força `saldo = 0`
- Atualizar conta valida `dia_fechamento ≠ dia_vencimento`

### `test_service_categoria.py`
- Criar categoria: duplicata de nome+tipo → ValueError
- Atualizar: nome duplicado ignorando o próprio ID
- Excluir: categoria em uso → ValueError

### `test_service_delegacao.py`
- Criar delegação: convite enviado com token único
- Aceitar convite: status muda para active
- Revogar: status muda para revoked

### `test_service_meta.py`
- Criar, atualizar e excluir metas
- `valor_atual` calculado via `recalcular_meta`

### `test_service_orcamento.py`
- Criar, atualizar e excluir orçamentos
- `valor_gasto` calculado via `recalcular_orcamento_mes`
