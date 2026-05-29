# Frontend

## Stack
- Vue 3
- TypeScript
- Pinia
- Vue Router
- Axios
- Tailwind CSS
- DaisyUI
- Vitest (unit)
- Playwright (E2E — `e2e/`)

## Estrutura relevante
- `src/views/` telas por dominio
- `src/services/api.ts` cliente HTTP central com interceptors
- `src/router/index.ts` rotas e guards
- `src/stores/` estado global — cobrem todos os dominios de listagem:
  - `auth.ts` — usuario autenticado, token
  - `contas.ts` — lista de contas; `fetchPromise` dedup
  - `categorias.ts` — lista de categorias; `fetchPromise` dedup
  - `orcamentos.ts` — lista de orcamentos; aceita `{ mes, ano }` como params opcionais
  - `metas.ts` — lista de metas; `fetchPromise` dedup
  - `delegacoes.ts` — convites enviados/recebidos, actAsOptions, pendingInviteCount
- `src/types/index.ts` contratos principais; `src/types/pagination.ts` — `PageMeta` com `has_next`
- `src/utils/date.ts` normalizacao e formatacao de datas
- `e2e/` testes Playwright (auth, transacoes, fatura)
- `e2e/fixtures.ts` fixture `authed` — injecta token no localStorage e mocka `/auth/me`

## Padrões de UI e estado
- Reaproveite padroes visuais entre telas antes de criar uma terceira variacao.
- Filtros de listagem normalmente vivem em query string e devem ser preservados em navegacoes de ida/volta.
- Requests devem passar pelo cliente central em `services/api.ts`.
- Contexto de delegacao usa `X-Act-As-User` no interceptor; nao contorne isso em chamadas isoladas.
- Tipagens devem acompanhar qualquer mudanca de contrato da API.

## Regra de stores e chamadas de API

Chamadas `api.get()` para listagem de recursos **nunca** devem ficar nas views. Use a store do dominio:

```typescript
// ERRADO — chamada direta na view
const res = await api.get('/contas')
contas.value = res.data

// CORRETO — via store
const contasStore = useContasStore()
const { contas } = storeToRefs(contasStore)
await contasStore.fetchContas()
```

Todas as stores extraem `.data` da resposta paginada internamente:
```typescript
contas.value = (res.data as { data: Conta[] }).data
```

O `storeToRefs(store)` e obrigatorio para manter reatividade no template. Destructuring direto perde reatividade.

## Contrato de resposta paginada

Todos os endpoints de listagem retornam:
```typescript
{ data: T[], meta: PageMeta }
// PageMeta: { page, page_size, total, total_pages, has_next }
```

`PageMeta` esta em `src/types/pagination.ts`. O campo `has_next: boolean` e usado para paginacao infinita/cursor.

## fetchPromise — padrao de dedup

Stores de dados imutaveis de sessao (contas, categorias, metas) usam `fetchPromise` para evitar chamadas duplicadas concorrentes:

```typescript
let fetchPromise: Promise<void> | null = null
async function fetchContas(): Promise<void> {
  if (fetchPromise) return fetchPromise
  loading.value = true
  fetchPromise = api.get('/contas').then((res) => {
    contas.value = (res.data as { data: Conta[] }).data
  }).finally(() => { loading.value = false; fetchPromise = null })
  return fetchPromise
}
```

Use este padrao sempre que multiplos componentes puderem chamar o mesmo fetch simultaneamente.

## DaisyUI e design system atual
- Preferir componentes DaisyUI para `btn`, `card`, `modal`, `alert`, `tabs`, `badge`, `dropdown`, `footer`.
- Evitar `alert()` e `confirm()` nativos; isso ja esta identificado como backlog tecnico/UX.
- Manter consistencia com o visual atual do produto em vez de introduzir outro micro-design-system local.

## Regras importantes de implementacao
- Ao trabalhar com datas vindas da API, usar `src/utils/date.ts` para evitar regressao de timezone.
- Ao abrir tela de edicao a partir de listas filtradas, preserve query string quando isso fizer parte do fluxo do usuario.
- Formularios de transacao, conta, meta e orcamento tem regra de negocio implicita; nao simplificar campos sem revisar impacto.
- Em telas financeiras, sempre considerar status (`previsto`, `liquidado`, `atrasado`, `cancelado`) e valor efetivo.

## Validacao
- Tipagem:
  - `npm run lint`
- Testes unitarios:
  - `npm run test`
- Testes E2E (Playwright):
  - `npm run test:e2e` (inicia dev server automaticamente)
  - `npm run test:e2e:ui` (modo interativo)

## Playwright — boas praticas
- Rotas sao processadas em LIFO: registre as mais gerais primeiro, as mais especificas por ultimo.
- O fixture `authed` ja registra catch-all para `/api/v1/` e mock de `/auth/me`; testes apenas sobrescrevem o necessario.
- Ao usar `storeToRefs(store)` para estado Pinia reativo no template; destructuring direto perde reatividade.
- Evitar `getByText()` sem `.first()` quando o texto pode aparecer em multiplos elementos (ex: nome em tabela e header).

## Serviços utilitários
- `src/services/storage.ts` — **única fonte de acesso ao localStorage**. Nunca usar `localStorage.*` diretamente. Métodos disponíveis:
  - **Token:** `getToken()`, `setToken(v)`, `removeToken()`
  - **Expiração:** `getTokenExpiresAt()`, `setTokenExpiresAt(v)`, `removeTokenExpiresAt()`
  - **Sessão:** `getSessionTimeout()`, `setSessionTimeout(v)`, `getLastActivity()`, `setLastActivity(v)`
  - **Delegação:** `getActAsUser()`, `removeActAsUser()`
  - **Importação:** `getImportHistory()`, `setImportHistory(v)`
  - **Limpar:** `clearSession()` — remove token, expiração, timeout, atividade e act-as
- `src/services/apiError.ts` — helper `extractApiError(err, fallback?)` para extrair mensagem legível de erros Axios (suporta `detail` string, array Pydantic e objeto com `msg`). Usar em todos os `catch` que exibem erro ao usuário.

## O que evitar
- Nao fazer chamadas `api.get` diretas para listagem quando existe store do dominio.
- Nao duplicar logica de filtro no componente se ela puder viver em helper isolado.
- Nao introduzir componentes novos para um padrao ja resolvido com DaisyUI.
- Nao manipular data com `new Date(string)` em fluxo sensivel sem revisar utilitarios existentes.
- Nao usar `localStorage.*` diretamente — sempre via `storage.*` de `src/services/storage.ts`.

## Direcao arquitetural
- Stores de dominio cobrem todas as listagens. Proximo passo: reducao de estado local residual em views de edicao/criacao (ex: `transacoes`, `contas`).
- Reaproveitar estruturas prontas da lista de transacoes, cards de resumo e fluxos de navegacao contextual.
- Consulte `docs/Plano_Evolucao_Arquitetural_Financas_Project.md` para o roadmap completo.
