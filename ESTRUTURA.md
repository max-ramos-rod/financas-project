# Estrutura do Projeto

## Raiz

```
financas-project/
├── backend/
├── frontend/
├── docker-compose.yml          # sobe db + backend + frontend em produção
├── CLAUDE.md
├── ESTRUTURA.md
├── INSTALACAO.md
├── QUICKSTART.md
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
│   │           ├── auth.py             # login, registro, refresh
│   │           ├── categorias.py       # CRUD categorias
│   │           ├── contas.py           # CRUD contas + fatura do cartão
│   │           ├── delegacoes.py       # convite, aceite, revogação, impersonação
│   │           ├── metas.py            # CRUD metas
│   │           ├── orcamentos.py       # CRUD orçamentos
│   │           ├── relatorios.py       # DRE mensal + export CSV/PDF
│   │           └── transacoes.py       # CRUD + visão-financeira + duplicar
│   ├── core/
│   │   ├── config.py
│   │   └── security.py                 # JWT + bcrypt
│   ├── crud/
│   │   ├── crud_categoria.py
│   │   ├── crud_conta.py               # validações de cartão, saldo forçado
│   │   ├── crud_delegacao.py
│   │   ├── crud_meta.py
│   │   ├── crud_orcamento.py
│   │   ├── crud_transacao.py           # saldo, dízimo, parcelamento, metas, orçamentos
│   │   └── crud_user.py
│   ├── db/
│   │   └── session.py                  # SQLAlchemy Session factory
│   ├── domain/
│   │   └── cartao_fatura.py            # cálculo de ciclos e faturas de cartão
│   ├── models/
│   │   ├── financeiro.py               # Conta, Transacao, Meta, Orcamento, Categoria, Delegacao
│   │   └── user.py
│   ├── schemas/
│   │   ├── categoria.py
│   │   ├── conta.py                    # validação dia_fechamento ≠ dia_vencimento; FaturaResumoResponse
│   │   ├── delegacao.py
│   │   ├── meta.py
│   │   ├── orcamento.py
│   │   ├── relatorio.py                # DREMensalResponse, DRECategoriaResumo
│   │   ├── transacao.py                # TransacaoCreate com validator; TransacaoFinanceiraResponse
│   │   └── user.py
│   ├── services/
│   │   └── email.py                    # envio de convites via SMTP
│   └── main.py
├── alembic/
│   └── versions/                       # migrations versionadas
├── tests/
│   ├── conftest.py                     # banco SQLite em memória + fixtures
│   ├── test_auth.py
│   ├── test_cartao_fatura_ciclo.py
│   ├── test_contas_cartao.py
│   ├── test_contas_fatura.py
│   ├── test_endpoints_smoke.py
│   ├── test_relatorios_dre.py
│   ├── test_transacoes_cartao_meta_orcamento.py
│   └── test_transacoes_filtros.py
├── seed_categorias.py                  # popula 44 categorias padrão
├── Dockerfile                          # imagem de produção com Gunicorn
├── requirements.txt
└── .env.example
```

### Rotas da API (prefixo `/api/v1`)

| Prefixo | Destaques |
|---|---|
| `/auth` | login, registro |
| `/contas` | CRUD + fatura atual/fechada + ajuste de ciclo + pagar fatura |
| `/transacoes` | CRUD + `/visao-financeira` (mescla transações com itens de fatura) + `/duplicar` |
| `/relatorios` | `/dre-mensal` + export CSV + export PDF |
| `/delegacoes` | invite, accept, revoke, act-as-options, confirm via token |
| `/metas` | CRUD |
| `/orcamentos` | CRUD |
| `/categorias` | CRUD |

## Frontend

```
frontend/
├── src/
│   ├── assets/
│   │   ├── style.css                   # Tailwind base + utilitários globais
│   │   └── tokens.css                  # variáveis CSS de design (cor, tipo, sombra)
│   ├── components/
│   │   ├── BrandMark.vue               # F mark SVG reutilizável
│   │   ├── ConfirmModal.vue            # modal de confirmação (4 severidades)
│   │   ├── EmptyState.vue              # estado vazio (4 variantes)
│   │   ├── Footer.vue
│   │   ├── Lockup.vue                  # lockup tipográfico (mark + texto)
│   │   ├── Navbar.vue
│   │   └── charts/
│   │       ├── DespesasCategoriaChart.vue     # ApexCharts · bar horizontal
│   │       ├── FluxoFinanceiroChart.vue       # ApexCharts · line/area
│   │       └── OrcamentoComparativoChart.vue  # HTML/CSS · lista com barras de progresso
│   ├── composables/
│   │   └── useAuth.ts                  # wrapper de conveniência sobre o store de auth
│   ├── router/
│   │   └── index.ts                    # rotas + guards de autenticação
│   ├── services/
│   │   └── api.ts                      # cliente Axios central com interceptors
│   ├── stores/
│   │   └── auth.ts                     # Pinia — estado de autenticação
│   ├── types/
│   │   └── index.ts                    # contratos TypeScript da API
│   ├── utils/
│   │   ├── chartTheme.ts               # tema light/dark para ApexCharts
│   │   ├── date.ts                     # normalização e formatação de datas
│   │   └── strings.ts                  # glossário PT-BR centralizado (LABELS)
│   ├── views/
│   │   ├── Auth/
│   │   │   ├── LoginView.vue
│   │   │   └── RegistroView.vue
│   │   ├── Categorias/
│   │   │   └── ListaCategoriasView.vue
│   │   ├── Contas/
│   │   │   ├── FaturaCartaoView.vue    # fatura por competência + ajuste de ciclo + editar itens
│   │   │   ├── ListaContasView.vue
│   │   │   └── NovaContaView.vue       # validação frontend: dia_fechamento ≠ dia_vencimento
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
│   │   │   ├── ListaTransacoesView.vue # tabela responsiva sm/md/lg com colunas progressivas
│   │   │   ├── NovaTransacaoView.vue   # redirect pós-salvar para fatura se veio de lá
│   │   │   ├── transacoesFetch.ts      # lógica de fetch + params para /visao-financeira
│   │   │   └── transacoesLoadControl.ts # debounce + hidratação inicial via query string
│   │   └── HomeView.vue
│   ├── App.vue
│   └── main.ts
├── public/
│   └── favicon.svg                     # F mark SVG
├── nginx.conf                          # config Nginx para SPA (fallback para index.html)
├── Dockerfile                          # build multi-stage Node → Nginx
├── index.html
├── package.json
├── tailwind.config.js                  # tema DaisyUI customizado: Forest #1F5C3A + escala tipográfica
├── tsconfig.json
└── vite.config.ts
```

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
- UNIQUE(conta_id, competencia_ano, competencia_mes) — um ajuste por período

### Meta
- `valor_alvo`, `valor_atual` (atualizado automaticamente), `data_inicio`, `data_fim`
- `concluida`, `cor`
- Atualizada automaticamente ao criar/editar transações vinculadas

### Orcamento
- `categoria_id`, `valor_planejado`, `valor_gasto` (calculado), `mes`, `ano`
- Atualizado automaticamente ao criar/editar transações da categoria

### Delegacao
- Compartilhamento de acesso entre usuários via convite por e-mail
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
