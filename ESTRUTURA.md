# Estrutura do Projeto

## Raiz

```
financas-project/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI: backend (PostgreSQL), frontend lint/unit, E2E Playwright
├── backend/
├── frontend/
├── docs/
│   ├── arquitetura/
│   │   ├── service-audit.md
│   │   └── transaction-map.md
│   ├── Plano_Evolucao_Arquitetural_Financas_Project.md
│   └── plano-refatoracao-smart-audit.md
├── docker-compose.yml          # sobe db + backend + frontend em produção
├── CLAUDE.md
├── ESTRUTURA.md
├── INSTALACAO.md
├── QUICKSTART.md
├── ROADMAP.md
└── README.md
```

## Backend

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py                     # AccessContext, autenticação e delegação
│   │   └── v1/
│   │       ├── api.py                  # Roteador principal v1
│   │       └── endpoints/
│   │           ├── auth.py             # login, registro, refresh, forgot/reset-password
│   │           ├── busca.py            # GET /busca?q= — full-text em transações e contas
│   │           ├── categorias.py       # CRUD categorias
│   │           ├── contas.py           # CRUD contas + fatura do cartão + export PDF
│   │           ├── delegacoes.py       # convite, aceite, revogação, impersonação
│   │           ├── importacao.py       # POST /importacao/upload — OFX / XLSX / CNAB
│   │           ├── metas.py            # CRUD metas
│   │           ├── orcamentos.py       # CRUD orçamentos
│   │           ├── relatorios.py       # DRE mensal + export CSV/PDF
│   │           └── transacoes.py       # CRUD + visão-financeira + duplicar + export CSV
│   ├── contracts/                      # Protocol interfaces (contratos entre camadas)
│   │   ├── __init__.py
│   │   ├── categoria.py                # CategoriaRepositoryProtocol
│   │   ├── conta.py                    # ContaRepositoryProtocol
│   │   ├── delegacao.py                # DelegacaoRepositoryProtocol
│   │   ├── meta.py                     # MetaRepositoryProtocol
│   │   ├── orcamento.py                # OrcamentoRepositoryProtocol
│   │   └── transacao.py                # TransacaoRepositoryProtocol
│   ├── core/
│   │   ├── config.py                   # Settings (pydantic-settings)
│   │   ├── errors.py                   # Handlers RFC 7807: HTTPException, ValidationError, 500
│   │   ├── limiter.py                  # Rate limiting slowapi
│   │   ├── pagination.py               # PaginationParams, PageMeta, PaginationMetaBuilder
│   │   ├── repositories.py             # SQLAlchemyRepository[T] — base genérica (flush, não commit)
│   │   ├── responses.py                # PagedResponse[T], ResponseEnvelope[T], helpers
│   │   └── security.py                 # JWT + bcrypt
│   ├── crud/
│   │   ├── crud_categoria.py
│   │   ├── crud_conta.py               # validações de cartão, saldo forçado
│   │   ├── crud_delegacao.py
│   │   ├── crud_meta.py
│   │   ├── crud_orcamento.py
│   │   ├── crud_password_reset.py      # criar_token, buscar_token_valido, marcar_usado
│   │   ├── crud_transacao.py           # saldo, dízimo, parcelamento, metas, orçamentos
│   │   └── crud_user.py
│   ├── db/
│   │   └── session.py                  # SQLAlchemy Session factory
│   ├── domain/
│   │   ├── cartao_fatura.py            # cálculo de ciclos e faturas de cartão
│   │   └── transacao.py                # impacto_no_saldo, recalcular_meta, recalcular_orcamento_mes
│   ├── models/
│   │   ├── __init__.py                 # re-exporta todos os modelos + enums
│   │   ├── categoria.py
│   │   ├── configuracao_cristao.py
│   │   ├── conta.py
│   │   ├── delegacao.py
│   │   ├── enums.py                    # TipoTransacao, StatusLiquidacao, TipoConta, …
│   │   ├── meta.py
│   │   ├── orcamento.py
│   │   ├── password_reset_token.py
│   │   ├── transacao.py
│   │   └── user.py
│   ├── repositories/                   # Implementações concretas dos contratos
│   │   ├── __init__.py
│   │   ├── categoria.py                # CategoriaRepository
│   │   ├── conta.py                    # ContaRepository
│   │   ├── delegacao.py                # DelegacaoRepository
│   │   ├── meta.py                     # MetaRepository
│   │   ├── orcamento.py                # OrcamentoRepository
│   │   └── transacao.py                # TransacaoRepository
│   ├── schemas/
│   │   ├── categoria.py
│   │   ├── conta.py                    # validação dia_fechamento ≠ dia_vencimento; FaturaResumoResponse
│   │   ├── delegacao.py
│   │   ├── importacao.py               # ImportacaoResult, ImportacaoErro, TransacaoImportada
│   │   ├── meta.py
│   │   ├── orcamento.py
│   │   ├── relatorio.py                # DREMensalResponse, DRECategoriaResumo
│   │   ├── transacao.py                # TransacaoCreate com validator; TransacaoFinanceiraResponse
│   │   └── user.py
│   ├── services/
│   │   ├── categoria.py                # CategoriaService
│   │   ├── conta.py                    # ContaService
│   │   ├── delegacao.py                # DelegacaoService
│   │   ├── dizimo.py                   # criar_transacao_dizimo
│   │   ├── email.py                    # send_password_reset_email, send_convite_email
│   │   ├── importacao/                 # parser de extratos
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # TransacaoImportada, helpers de parse
│   │   │   ├── cnab_parser.py          # CNAB 240/400
│   │   │   ├── detector.py             # detectar_e_parsear (entry point)
│   │   │   ├── ofx_parser.py           # OFX/QIF
│   │   │   └── xlsx_parser.py          # XLSX/CSV
│   │   ├── meta.py                     # MetaService
│   │   ├── orcamento.py                # OrcamentoService
│   │   ├── parcelamento.py             # criar_parcelamento
│   │   ├── password_reset.py           # PasswordResetService
│   │   └── transacao.py                # TransacaoService
│   └── main.py                         # FastAPI + middleware + exception handlers
├── alembic/
│   └── versions/                       # migrations versionadas
├── tests/
│   ├── conftest.py                     # banco SQLite em memória + fixtures + disable_rate_limiting
│   ├── test_auth.py
│   ├── test_auth_password_reset.py     # forgot-password, reset-password, token expirado/usado
│   ├── test_auth_rate_limiting.py      # testa 429 com limiter habilitado
│   ├── test_busca.py                   # GET /busca, isolamento de usuário, min_length
│   ├── test_cartao_fatura_ciclo.py
│   ├── test_contas_cartao.py
│   ├── test_contas_fatura.py
│   ├── test_endpoints_smoke.py
│   ├── test_negativos.py               # acesso cruzado, IDs inválidos, operações proibidas
│   ├── test_relatorios_dre.py
│   ├── test_transacoes_cartao_meta_orcamento.py
│   ├── test_transacoes_filtros.py
│   └── unit/                           # testes unitários (sem banco, com fakes)
│       ├── conftest.py                 # FakeRepository, make_db, factories
│       ├── test_domain_transacao.py
│       ├── test_service_categoria.py
│       ├── test_service_conta.py
│       ├── test_service_delegacao.py
│       ├── test_service_meta.py
│       ├── test_service_orcamento.py
│       └── test_service_transacao.py
├── seed_categorias.py                  # popula 44 categorias padrão
├── Dockerfile                          # imagem de produção com Gunicorn
├── pyproject.toml                      # ruff + pytest config
├── requirements.txt
└── .env.example
```

### Rotas da API (prefixo `/api/v1`)

| Prefixo | Destaques |
|---|---|
| `/auth` | login, registro, refresh, `forgot-password`, `reset-password` |
| `/busca` | `GET ?q=` — full-text em transações e contas (≥ 2 chars, 10 results/tipo) |
| `/contas` | CRUD + fatura atual/fechada + ajuste de ciclo + pagar fatura + export PDF |
| `/transacoes` | CRUD + `/visao-financeira` + `/duplicar` + `/export` (CSV) |
| `/relatorios` | `/dre-mensal` + export CSV + export PDF |
| `/importacao` | `POST /upload` — OFX, XLSX, CNAB (≤ 5 MB) |
| `/delegacoes` | invite, accept, revoke, act-as-options, confirm via token |
| `/metas` | CRUD |
| `/orcamentos` | CRUD |
| `/categorias` | CRUD |

Endpoints especiais na raiz:

| Rota | Detalhe |
|---|---|
| `GET /` | status da API |
| `GET /health` | health check (usado pelo Docker) |

## Frontend

```
frontend/
├── src/
│   ├── assets/
│   │   ├── style.css                   # Tailwind base + utilitários globais
│   │   └── tokens.css                  # variáveis CSS de design (cor, tipo, sombra)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── BrandMark.vue           # F mark SVG reutilizável
│   │   │   ├── Footer.vue
│   │   │   ├── Lockup.vue              # lockup tipográfico (mark + texto)
│   │   │   └── Navbar.vue
│   │   ├── ui/
│   │   │   ├── ConfirmModal.vue        # modal de confirmação (4 severidades)
│   │   │   └── EmptyState.vue          # estado vazio (4 variantes)
│   │   ├── charts/
│   │   │   ├── DespesasCategoriaChart.vue     # ApexCharts · bar horizontal
│   │   │   ├── FluxoFinanceiroChart.vue       # ApexCharts · line/area
│   │   │   └── OrcamentoComparativoChart.vue  # HTML/CSS · barras de progresso
│   │   └── Transacoes/
│   │       ├── TransacoesFiltroBarra.vue       # toolbar de filtros extraída
│   │       └── TransacoesLista.vue             # tabela de transações extraída
│   ├── composables/
│   │   ├── useAuth.ts                  # wrapper de conveniência sobre o store de auth
│   │   └── useTransacoesFiltros.ts     # lógica de filtros com debounce
│   ├── router/
│   │   └── index.ts                    # rotas + guards de autenticação
│   ├── services/
│   │   ├── api.ts                      # cliente Axios central com interceptors
│   │   ├── apiError.ts                 # extractApiError(err, fallback?) — suporta detail string/array/objeto
│   │   └── storage.ts                  # única fonte de acesso ao localStorage
│   ├── stores/
│   │   ├── auth.ts                     # usuário autenticado, token, expiração de sessão
│   │   ├── categorias.ts               # lista + fetchPromise dedup
│   │   ├── contas.ts                   # lista + fetchPromise dedup
│   │   ├── delegacoes.ts               # convites, actAsOptions, pendingInviteCount
│   │   ├── metas.ts                    # lista + fetchPromise dedup
│   │   ├── orcamentos.ts               # lista com params opcionais { mes, ano }
│   │   └── transacoes.ts               # fetch em bloco para o Dashboard (page_size=500)
│   ├── types/
│   │   ├── auth.ts
│   │   ├── categorias.ts
│   │   ├── contas.ts
│   │   ├── delegacao.ts
│   │   ├── fatura.ts
│   │   ├── importacao.ts
│   │   ├── index.ts                    # re-exporta todos os tipos
│   │   ├── metas.ts
│   │   ├── orcamentos.ts
│   │   ├── pagination.ts               # PageMeta com has_next
│   │   ├── relatorios.ts
│   │   └── transacoes.ts
│   ├── utils/
│   │   ├── chartTheme.ts               # tema light/dark para ApexCharts
│   │   ├── date.ts                     # normalização e formatação de datas
│   │   ├── financeiro.ts               # helpers de cálculo financeiro
│   │   └── strings.ts                  # glossário PT-BR centralizado (LABELS)
│   ├── views/
│   │   ├── Auth/
│   │   │   ├── ForgotPasswordView.vue  # tela de recuperação de senha
│   │   │   ├── LoginView.vue
│   │   │   ├── RegistroView.vue
│   │   │   └── ResetPasswordView.vue   # tela de redefinição com token
│   │   ├── Busca/
│   │   │   └── BuscaView.vue           # busca global com debounce 300ms
│   │   ├── Categorias/
│   │   │   └── ListaCategoriasView.vue
│   │   ├── Contas/
│   │   │   ├── FaturaCartaoView.vue    # fatura por competência + ajuste de ciclo + export PDF
│   │   │   ├── ListaContasView.vue
│   │   │   └── NovaContaView.vue       # validação: dia_fechamento ≠ dia_vencimento
│   │   ├── Dashboard/
│   │   │   └── IndexView.vue           # grid 12 colunas, KPIs, 3 charts
│   │   ├── Delegacoes/
│   │   │   ├── ConfirmarConviteView.vue
│   │   │   ├── ConvidarDelegacaoView.vue
│   │   │   └── ConvitesView.vue
│   │   ├── Metas/
│   │   │   ├── ListaMetasView.vue
│   │   │   └── NovaMetaView.vue
│   │   ├── Orcamentos/
│   │   │   ├── ListaOrcamentosView.vue
│   │   │   └── NovoOrcamentoView.vue
│   │   ├── Relatorios/
│   │   │   └── ListaRelatoriosView.vue # DRE mensal + export CSV/PDF
│   │   ├── Transacoes/
│   │   │   ├── ImportacaoView.vue      # upload OFX/XLSX/CNAB com histórico local
│   │   │   ├── ListaTransacoesView.vue # tabela responsiva sm/md/lg + export CSV
│   │   │   ├── NovaTransacaoView.vue   # redirect pós-salvar para fatura se veio de lá
│   │   │   ├── transacoesFetch.ts      # monta params e chama /visao-financeira
│   │   │   ├── transacoesFetch.test.ts
│   │   │   ├── transacoesLoadControl.ts # debounce + hidratação via query string
│   │   │   └── transacoesLoadControl.test.ts
│   │   └── HomeView.vue
│   ├── __tests__/
│   │   ├── apiError.test.ts
│   │   └── storage.test.ts
│   ├── App.vue
│   └── main.ts
├── e2e/                                # Playwright E2E
│   ├── fixtures.ts                     # fixture authed — injeta token + mock /auth/me
│   ├── auth.spec.ts
│   ├── fatura.spec.ts
│   └── transacoes.spec.ts
├── public/
│   └── favicon.svg                     # F mark SVG
├── nginx.conf                          # config Nginx para SPA (fallback para index.html)
├── Dockerfile                          # build multi-stage Node → Nginx
├── index.html
├── package.json
├── playwright.config.ts
├── tailwind.config.js                  # tema DaisyUI customizado: Forest #1F5C3A + escala tipográfica
├── tsconfig.json
└── vite.config.ts
```

### Rotas do frontend

| Caminho | View | Auth |
|---|---|---|
| `/` | HomeView | pública |
| `/login` | LoginView | pública |
| `/registro` | RegistroView | pública |
| `/recuperar-senha` | ForgotPasswordView | pública |
| `/redefinir-senha` | ResetPasswordView | pública |
| `/convites/confirmar` | ConfirmarConviteView | pública |
| `/dashboard` | Dashboard/IndexView | sim |
| `/busca` | Busca/BuscaView | sim |
| `/transacoes` | ListaTransacoesView | sim |
| `/transacoes/nova` | NovaTransacaoView | sim |
| `/transacoes/importar` | ImportacaoView | sim |
| `/transacoes/:id/editar` | NovaTransacaoView | sim |
| `/contas` | ListaContasView | sim |
| `/contas/nova` | NovaContaView | sim |
| `/contas/:id/editar` | NovaContaView | sim |
| `/contas/:id/fatura` | FaturaCartaoView | sim |
| `/metas` | ListaMetasView | sim |
| `/metas/nova` | NovaMetaView | sim |
| `/metas/:id/editar` | NovaMetaView | sim |
| `/orcamentos` | ListaOrcamentosView | sim |
| `/orcamentos/novo` | NovoOrcamentoView | sim |
| `/orcamentos/:id/editar` | NovoOrcamentoView | sim |
| `/relatorios` | ListaRelatoriosView | sim |
| `/categorias` | ListaCategoriasView | sim |
| `/delegacoes/convidar` | ConvidarDelegacaoView | sim |
| `/delegacoes/convites` | ConvitesView | sim |

## Modelos principais

### Transacao
- `tipo`: entrada | saida
- `status_liquidacao`: previsto | liquidado | atrasado | cancelado
- `fixa`, `recorrente`, `parcelado`, `total_parcelas`, `parcela_atual`
- `tem_dizimo`, `percentual_dizimo`, `transacao_dizimo_uuid`, `e_dizimo`, `entrada_origem_id`
- `e_emprestimo`, `pessoa_emprestimo`
- `grupo_parcelamento_uuid`, `transacao_uuid`
- `valor_multa`, `valor_juros`, `valor_desconto`
- `item_tipo` (response): `'transacao'` | `'fatura_cartao'` — usado na visão financeira unificada

### Conta
- `tipo`: carteira | conta_corrente | poupanca | investimento | cartao_credito | outro
- Cartão: `dia_fechamento`, `dia_vencimento`, `limite_credito`
- Validação: `dia_fechamento ≠ dia_vencimento` (backend e frontend)
- Response inclui fatura aberta e fechada calculadas dinamicamente

### ContaCartaoCiclo
- Override de ciclo de fatura para competência específica: `conta_id`, `competencia_ano`, `competencia_mes`
- `data_fechamento_real`, `data_vencimento_real`, `observacao`
- UNIQUE(conta_id, competencia_ano, competencia_mes)

### PasswordResetToken
- `user_id`, `token` (urlsafe 32 bytes), `expires_at` (TTL 1h), `used_at`, `created_at`
- INDEX em `token`

### Meta
- `valor_alvo`, `valor_atual` (atualizado automaticamente), `data_inicio`, `data_fim`
- `concluida`, `cor`

### Orcamento
- `categoria_id`, `valor_planejado`, `valor_gasto` (calculado), `mes`, `ano`

### Delegacao
- Compartilhamento via convite por e-mail
- `status`: pending | active | revoked
- `can_write`: controla permissão de escrita do delegado
- Impersonação via header `X-Act-As-User` → `AccessContext` em `deps.py`

## Deploy (Docker Compose)

```
docker-compose.yml
  ├── db         PostgreSQL 17-alpine
  ├── backend    Gunicorn + UvicornWorker (2 workers) · porta 8000 interna
  └── frontend   Nginx servindo dist/ · porta 5173:80
```

Volumes e networks são externos (gerenciados fora do compose).

## CI/CD (.github/workflows/ci.yml)

3 jobs disparados em push/PR para `main`:

| Job | O que faz |
|---|---|
| `backend` | ruff check + pytest -q contra PostgreSQL 17 (service container) |
| `frontend` | vue-tsc --noEmit + vitest run |
| `e2e` | Playwright Chromium (depende de `frontend`); sobe dev server via webServer config |
