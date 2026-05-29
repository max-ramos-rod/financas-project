# Roadmap — Finanças Cristãs

Atualizado: maio 2026

---

## Concluído

### Produto
- [x] Transações: entradas, saídas, parcelamento, recorrência, dízimo automático
- [x] Múltiplas contas: carteira, banco, poupança, investimento, cartão de crédito
- [x] Cartão de crédito: ciclo de fatura, ajuste de ciclo por competência, pagamento de fatura
- [x] Categorias padrão (44) + customizadas por usuário
- [x] Orçamentos mensais com acompanhamento percentual
- [x] Metas financeiras com progresso acumulado
- [x] DRE mensal com exportação CSV e PDF
- [x] Delegação de acesso: convite, aceite, revogação, impersonação via `X-Act-As-User`
- [x] Duplicar transação
- [x] Busca global (`GET /busca?q=`) — transações e contas, debounce 300ms no frontend
- [x] Importação de extratos: OFX, XLSX, CNAB (upload com detecção automática de formato)
- [x] Export CSV de transações com filtros
- [x] Export PDF de fatura do cartão

### Segurança e qualidade
- [x] Rate limiting em endpoints de autenticação (slowapi)
- [x] Recuperação de senha via e-mail (`/auth/forgot-password` + `/auth/reset-password`)
- [x] Sessão por inatividade configurável (`SESSION_INACTIVITY_MINUTES` no `.env`)
- [x] Erros padronizados no formato RFC 7807
- [x] Envelope de resposta padronizado (`PagedResponse[T]`) em todos os endpoints de listagem
- [x] Paginação reutilizável (`PaginationParams`, `PaginationMetaBuilder`)
- [x] Ruff linting ativo no backend
- [x] CI/CD GitHub Actions (backend + frontend lint/unit + Playwright E2E)
- [x] Testes E2E Playwright (auth, transações, fatura)

### Frontend / Design
- [x] Redesign completo: tema DaisyUI customizado (Forest `#1F5C3A`), Geist + Geist Mono
- [x] Tokens de design CSS (`tokens.css`) + escala tipográfica semântica
- [x] Componentes `BrandMark`, `Lockup`, `EmptyState`, `ConfirmModal`
- [x] Dashboard em grid 12 colunas: KPIs, fluxo financeiro, despesas, orçamento
- [x] Home e Login redesenhados
- [x] Glossário PT-BR centralizado (`LABELS` em `strings.ts`)
- [x] Tema ApexCharts consistente com o design system
- [x] Tabela de transações responsiva com colunas progressivas (sm/md/lg)
- [x] Hi-fi das telas Contas, Metas e Orçamentos
- [x] `storage.ts` — único ponto de acesso ao `localStorage`
- [x] `apiError.ts` — helper `extractApiError(err)` para erros Axios
- [x] Stores Pinia por domínio: auth, contas, categorias, orcamentos, metas, delegacoes, transacoes

### Arquitetura
- [x] Service layer parcial: `TransacaoService`, `ContaService`, `CategoriaService`, `DelegacaoService`, `MetaService`, `OrcamentoService`
- [x] Services auxiliares: `DizimoService`, `ParcelamentoService`, `ImportacaoService`
- [x] Repositories concretos: `TransacaoRepository`, `ContaRepository`, `CategoriaRepository`, `DelegacaoRepository`, `MetaRepository`, `OrcamentoRepository`
- [x] Contratos de interface (`Protocol`): `app/contracts/`
- [x] Domain layer: `app/domain/cartao_fatura.py`, `app/domain/transacao.py`
- [x] Testes unitários de service com fakes: `tests/unit/` (7 suites)

---

## Próximo — Produto

### Dark mode
Tokens de CSS já preparados. Falta: switch de tema na UI, ajuste dos componentes para dark, persistência da preferência.
- Dificuldade: média · Impacto: médio

### Onboarding
Fluxo guiado para novo usuário: criar primeira conta → lançar primeira transação → ver o dashboard.
Placeholder de EmptyState já existe.
- Dificuldade: média · Impacto: alto

### Login com Google / OAuth
Autenticação social integrada ao fluxo JWT atual. Model `User` já tem campos `google_id` e `google_email`.
- Dificuldade: média · Impacto: médio-alto

### SMTP para recuperação de senha
Integração completa — por ora o token é logado em nível INFO (`[DEV]`). `send_password_reset_email` já existe em `app/services/email.py`.
- Dificuldade: baixa · Impacto: alto

### Substituição de alert()/confirm() nativos
Backlog técnico: trocar os remanescentes por `<ConfirmModal>` ou toast inline.
- Dificuldade: baixa · Impacto: médio (UX)

---

## Médio prazo — Arquitetura

### Testes unitários de service — cobertura completa
Expandir `tests/unit/` para cobrir todos os branches críticos dos services existentes.
- Dificuldade: média · Impacto: muito alto

### Reduzir lógica residual em views
CRUD direto (POST/PUT/DELETE) e estado de edição em `transacoes`, `contas`, `metas` ainda vivem nas views. Candidatos a migrar para stores ou composables.
- Dificuldade: média · Impacto: alto

---

## Longo prazo

### Observabilidade
Logs estruturados, correlation ID, health checks mais ricos com status do banco.
- Dificuldade: média · Sem dependência forte

### Migração async (avaliação)
Revisar se há ganho real por módulo antes de migrar.
Só faz sentido após a service layer estar estabilizada.
- Dificuldade: alta · Dependência: service layer + repositories

---

## Referências

- Plano arquitetural detalhado: `docs/Plano_Evolucao_Arquitetural_Financas_Project.md`
- Handoff do redesign (fases 0–9): `frontend/handoff/tasks.md`
- Plano de refatoração smart-audit: `docs/plano-refatoracao-smart-audit.md`
