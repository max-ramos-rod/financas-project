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

### Frontend / Design
- [x] Redesign completo: tema DaisyUI customizado (Forest `#1F5C3A`), Geist + Geist Mono
- [x] Tokens de design CSS (`tokens.css`) + escala tipográfica semântica
- [x] Componentes `BrandMark`, `Lockup`, `EmptyState`, `ConfirmModal`
- [x] Dashboard em grid 12 colunas: KPIs, fluxo financeiro, despesas, orçamento
- [x] Home e Login redesenhados
- [x] Glossário PT-BR centralizado (`LABELS` em `strings.ts`)
- [x] Tema ApexCharts consistente com o design system
- [x] Tabela de transações responsiva com colunas progressivas (sm/md/lg)
- [x] Hi-fi das telas Contas, Metas e Orçamentos: cabeçalho inline, KPI strip, toolbar de filtros, EmptyState, ConfirmModal
- [x] Lighthouse acessibilidade ≥ 95 (Home 95 · Login 96)

### Backend / Qualidade
- [x] Validação `dia_fechamento ≠ dia_vencimento` no cartão (backend + frontend)
- [x] Validador de parcelamento movido para `TransacaoCreate` (corrige 500 na listagem)
- [x] Suite de testes cobrindo auth, contas, fatura, DRE, filtros, parcelamento, metas, orçamentos
- [x] Testes com datas relativas (não quebram com o tempo)

---

## Próximo — Produto

### Sessão por inatividade
Expirar sessão automaticamente após período configurável no `.env`.
Segurança básica para uso em dispositivos compartilhados.
- Dificuldade: média · Impacto: alto · Dependências: nenhuma

### Dark mode
Tokens de CSS já preparados. Falta: switch de tema na UI, ajuste dos componentes para dark, persistência da preferência.
- Dificuldade: média · Impacto: médio

### Onboarding
Fluxo guiado para novo usuário: criar primeira conta → lançar primeira transação → ver o dashboard.
Placeholder de EmptyState já existe.
- Dificuldade: média · Impacto: alto

### Login com Google / OAuth
Autenticação social integrada ao fluxo JWT atual.
- Dificuldade: média · Impacto: médio-alto · Dependências: nenhuma estrutural

---

## Próximo — Qualidade técnica

### Contratos de API padronizados
`SuccessResponse`, `PaginatedResponse`, `PaginationMeta` no backend.
Erros no formato RFC 7807 (`problem+json`).
Adapter no cliente HTTP do frontend.
- Dificuldade: média · Impacto: alto

### Paginação nas listagens
`PaginationParams` e `Page` reutilizáveis.
Frontend com scroll infinito ou paginação explícita nas telas de transações e relatórios.
- Dificuldade: baixa-média · Dependência: contratos de API

### Stores por domínio (frontend)
Reduzir lógica nas views, centralizar estado/erro/loading por domínio (transações, contas, metas).
- Dificuldade: média · Impacto: alto

---

## Médio prazo — Arquitetura

### Service layer
Separar orquestração de negócio da persistência.
Começar por `TransacaoService` (módulo mais crítico e com mais efeitos colaterais).
- Dificuldade: alta · Impacto: muito alto
- Referência: `docs/Plano_Evolucao_Arquitetural_Financas_Project.md` § Fase 2

### Repositories explícitos
Mover queries SQLAlchemy para camada dedicada.
Services dependendo de interfaces (`Protocol`).
- Dificuldade: alta · Dependência: `TransacaoService`

### Testes unitários de service
Testar regras de negócio sem banco usando fakes de repositories.
- Dificuldade: média · Impacto: muito alto · Dependência: repositories + Protocol

### Subserviços de domínio
Extrair de `crud_transacao.py`: `SaldoService`, política de orçamento, atualização de metas, regras de dízimo, política de cartão.
- Dificuldade: média-alta · Dependência: service layer estabilizada

---

## Longo prazo

### Observabilidade
Logs estruturados, correlation ID, health checks mais ricos.
- Dificuldade: média · Sem dependência forte

### Migração async (avaliação)
Revisar se há ganho real por módulo antes de migrar.
Só faz sentido após a arquitetura estar desacoplada.
- Dificuldade: alta · Dependência: service layer + repositories

### ~~Hi-fi das telas restantes~~ ✅ Concluído
Todas as telas principais foram redesenhadas: Dashboard, Home, Login, Transações, Contas, Metas, Orçamentos.

---

## Referências

- Plano arquitetural detalhado: `docs/Plano_Evolucao_Arquitetural_Financas_Project.md`
- Handoff do redesign (fases 0–9): `frontend/handoff/tasks.md`
