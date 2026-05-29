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
- `src/stores/` estado global
- `src/types/index.ts` contratos principais
- `src/utils/date.ts` normalizacao e formatacao de datas
- `e2e/` testes Playwright (auth, transacoes, fatura)
- `e2e/fixtures.ts` fixture `authed` — injecta token no localStorage e mocka `/auth/me`

## Padrões de UI e estado
- Reaproveite padroes visuais entre telas antes de criar uma terceira variacao.
- Filtros de listagem normalmente vivem em query string e devem ser preservados em navegacoes de ida/volta.
- Requests devem passar pelo cliente central em `services/api.ts`.
- Contexto de delegacao usa `X-Act-As-User` no interceptor; nao contorne isso em chamadas isoladas.
- Tipagens devem acompanhar qualquer mudanca de contrato da API.

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

## O que evitar
- Nao fazer chamadas Axios diretas espalhadas quando ja existe helper/fetch do dominio.
- Nao duplicar logica de filtro no componente se ela puder viver em helper isolado.
- Nao introduzir componentes novos para um padrao ja resolvido com DaisyUI.
- Nao manipular data com `new Date(string)` em fluxo sensivel sem revisar utilitarios existentes.

## Direcao arquitetural
- Continuar movendo logica demais das views para helpers/stores por dominio.
- Reaproveitar estruturas prontas da lista de transacoes, cards de resumo e fluxos de navegacao contextual.
