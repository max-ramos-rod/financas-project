# Frontend — Finanças Cristãs

Vue 3 + TypeScript + TailwindCSS + DaisyUI + Pinia + ApexCharts

## Instalação

```bash
cd frontend
npm install
cp .env.example .env
```

`.env`:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Desenvolvimento

```bash
npm run dev      # http://localhost:5173
npm run build    # build de produção
```

## Validação

```bash
npm run lint         # vue-tsc --noEmit
npm run test         # vitest run
npm run test:e2e     # Playwright (inicia dev server automaticamente)
npm run test:e2e:ui  # Playwright modo interativo
```

## Estrutura relevante

| Caminho | Responsabilidade |
|---|---|
| `src/assets/style.css` | Tailwind base + utilitários globais |
| `src/assets/tokens.css` | Variáveis CSS de design (cor, tipografia, sombra) — importado em `main.ts` |
| `src/services/api.ts` | Cliente Axios central com interceptors (inclui `X-Act-As-User` para delegação) |
| `src/services/storage.ts` | **Único ponto de acesso ao localStorage** — nunca usar `localStorage.*` diretamente |
| `src/services/apiError.ts` | `extractApiError(err, fallback?)` — extrai mensagem de erros Axios (string/array Pydantic/objeto) |
| `src/router/index.ts` | Rotas + guards de autenticação |
| `src/stores/auth.ts` | Estado global de autenticação (Pinia) |
| `src/stores/contas.ts` | Lista de contas com `fetchPromise` dedup |
| `src/stores/categorias.ts` | Lista de categorias com `fetchPromise` dedup |
| `src/stores/orcamentos.ts` | Lista de orçamentos com params `{ mes, ano }` opcionais |
| `src/stores/metas.ts` | Lista de metas com `fetchPromise` dedup |
| `src/stores/delegacoes.ts` | Convites, actAsOptions, pendingInviteCount |
| `src/stores/transacoes.ts` | Fetch em bloco para o Dashboard (page_size=500) |
| `src/composables/useAuth.ts` | Wrapper de conveniência sobre o store de auth |
| `src/composables/useTransacoesFiltros.ts` | Lógica de filtros de transações com debounce |
| `src/types/index.ts` | Re-exporta todos os contratos TypeScript |
| `src/types/pagination.ts` | `PageMeta` com `has_next: boolean` |
| `src/utils/strings.ts` | Glossário PT-BR centralizado (`LABELS`) — strings visíveis ao usuário |
| `src/utils/date.ts` | Normalização e formatação de datas (evita bugs de timezone) |
| `src/utils/financeiro.ts` | Helpers de cálculo financeiro |
| `src/utils/chartTheme.ts` | Tema light/dark para ApexCharts (`getChartTheme()`) |
| `src/components/ui/ConfirmModal.vue` | Modal de confirmação reutilizável (4 severidades) |
| `src/components/ui/EmptyState.vue` | Estado vazio (4 variantes: first-time, filtered, error, zero-state) |
| `src/components/layout/` | BrandMark, Lockup, Navbar, Footer |
| `src/components/Transacoes/` | TransacoesFiltroBarra, TransacoesLista |
| `src/views/Transacoes/transacoesFetch.ts` | Monta params e chama `/visao-financeira` |
| `src/views/Transacoes/transacoesLoadControl.ts` | Inicialização + debounce de filtros via query string |
| `e2e/fixtures.ts` | Fixture `authed` — injeta token e mocka `/auth/me` para testes Playwright |

## Padrões importantes

- Todas as chamadas HTTP passam por `services/api.ts` — nunca usar Axios direto nas views
- Datas da API sempre processadas via `src/utils/date.ts`
- Strings PT-BR visíveis ao usuário usam `LABELS` de `utils/strings.ts`
- Filtros de listagem vivem na query string e são preservados em navegações (ida/volta)
- Delegação de acesso usa `X-Act-As-User` via interceptor — não contornar com chamadas isoladas
- Tokens de design CSS (`--brand`, `--ink`, `--surface`, etc.) ficam em `tokens.css`; não duplicar inline
- Usar `storeToRefs(store)` para manter reatividade ao destructurar stores; destructuring direto perde reatividade

## Design system

O tema DaisyUI foi customizado em `tailwind.config.js`:
- Cor primary: `#1F5C3A` (Forest)
- Tipografia: Geist (sans) + Geist Mono (labels técnicos)
- Escala semântica: `text-label`, `text-meta`, `text-body`, `text-lg`, ... `text-display`, `text-mega`
- Componentes de marca: `<BrandMark>` (F mark SVG) e `<Lockup>` (mark + texto)

## Padrão de telas

Todas as telas de listagem (Transações, Contas, Metas, Orçamentos) seguem o mesmo padrão:
1. **Cabeçalho inline** — título semântico + contador + CTA principal, sem barra separada
2. **Toolbar de filtros** — `card bg-base-100 shadow-sm` com busca, segmented control e selects
3. **KPI strip** — `grid grid-cols-2 lg:grid-cols-4` com cards de métricas e valores `tabular-nums`
4. **Conteúdo principal** — lista/tabela/cards em `card bg-base-100 shadow-sm`
5. **EmptyState** — variante `first-time` (sem dados) ou `filtered` (sem resultados com filtros)
6. **ConfirmModal** — substitui `alert()`/`confirm()` nativos em todas as ações destrutivas
