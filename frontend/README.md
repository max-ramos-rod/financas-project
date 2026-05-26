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
npm run lint     # vue-tsc --noEmit
npm run test     # vitest run
```

## Estrutura relevante

| Caminho | Responsabilidade |
|---|---|
| `src/assets/style.css` | Tailwind base + utilitários globais |
| `src/assets/tokens.css` | Variáveis CSS de design (cor, tipografia, sombra) — importado em `main.ts` |
| `src/services/api.ts` | Cliente Axios central com interceptors (inclui `X-Act-As-User` para delegação) |
| `src/router/index.ts` | Rotas + guards de autenticação |
| `src/stores/auth.ts` | Estado global de autenticação (Pinia) |
| `src/composables/useAuth.ts` | Wrapper de conveniência sobre o store de auth |
| `src/types/index.ts` | Contratos TypeScript que espelham os schemas da API |
| `src/utils/strings.ts` | Glossário PT-BR centralizado (`LABELS`) — strings visíveis ao usuário |
| `src/utils/date.ts` | Normalização e formatação de datas (evita bugs de timezone) |
| `src/utils/chartTheme.ts` | Tema light/dark para ApexCharts (`getChartTheme()`) |
| `src/components/ConfirmModal.vue` | Modal de confirmação reutilizável (4 severidades) |
| `src/components/EmptyState.vue` | Estado vazio (4 variantes: first-time, filtered, error, zero-state) |
| `src/views/Transacoes/transacoesFetch.ts` | Monta params e chama `/visao-financeira` |
| `src/views/Transacoes/transacoesLoadControl.ts` | Inicialização + debounce de filtros via query string |

## Padrões importantes

- Todas as chamadas HTTP passam por `services/api.ts` — nunca usar Axios direto nas views
- Datas da API sempre processadas via `src/utils/date.ts`
- Strings PT-BR visíveis ao usuário usam `LABELS` de `utils/strings.ts`
- Filtros de listagem vivem na query string e são preservados em navegações (ida/volta)
- Delegação de acesso usa `X-Act-As-User` via interceptor — não contornar com chamadas isoladas
- Tokens de design CSS (`--brand`, `--ink`, `--surface`, etc.) ficam em `tokens.css`; não duplicar inline

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
