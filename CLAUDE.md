# financas-project

## Estrutura do monorepo
- `backend/` API FastAPI + SQLAlchemy + Alembic + PostgreSQL
- `frontend/` SPA Vue 3 + TypeScript + Pinia + Vue Router + Axios + Tailwind + DaisyUI
- `nginx/` proxy reverso e configuração de deploy
- `docs/` documentação de apoio

## Como usar este monorepo
- O projeto nao usa workspace manager na raiz.
- Comandos de backend devem ser rodados dentro de `backend/`.
- Comandos de frontend devem ser rodados dentro de `frontend/`.
- Deploy local/servidor costuma passar por `docker-compose.yml`.

## Regras universais
- Preserve os fluxos de negocio existentes antes de tentar "limpar" arquitetura.
- Evite reescritas amplas. Prefira mudanças incrementais e testaveis.
- Nao commitar secrets, tokens ou credenciais reais.
- Sempre considerar impacto em dados financeiros, saldos, orcamentos, metas e faturas.
- Quando mexer com datas, validar comportamento de timezone e serializacao entre backend e frontend.
- Ao alterar contratos da API, ajustar tipagem frontend e testes no mesmo ciclo.

## Convencoes de validacao
- Backend:
  - `cd backend`
  - `.\venv\Scripts\python.exe -m pytest -q`
- Frontend:
  - `cd frontend`
  - `npm run lint`
  - `npm run test`
  - `npm run test:e2e` (Playwright; requer dev server em http://localhost:5173)

## Fronteiras de escopo
- Mudancas em `frontend/` nao devem alterar `backend/` sem necessidade explicita.
- Mudancas em `backend/` que alterem response shape devem atualizar consumidor frontend.
- Evite tocar em `nginx/` ou `docker-compose.yml` em tarefas puramente funcionais.

## Arquitetura atual que deve ser respeitada

### Backend
- Padrao predominante: `api -> service -> repository -> db` para dominios migrados; `api -> crud_* -> db` para endpoints residuais.
- `app/core/` contem infra transversal: `pagination.py` (PaginationParams, PageMeta, PaginationMetaBuilder), `responses.py` (PagedResponse, ResponseEnvelope), `errors.py` (handlers RFC 7807), `limiter.py` (rate limiting slowapi), `repositories.py` (SQLAlchemyRepository base — flush, nao commit).
- `app/contracts/` — Protocol interfaces (CategoriaRepositoryProtocol, ContaRepositoryProtocol, etc.); definem o contrato entre services e repositories.
- `app/repositories/` — implementacoes concretas dos contratos (CategoriaRepository, ContaRepository, etc.).
- `app/services/` — orchestracao de negocio por dominio (TransacaoService, ContaService, CategoriaService, MetaService, OrcamentoService, DelegacaoService, DizimoService, ParcelamentoService); `importacao/` para upload de extratos.
- `app/domain/` — regras de dominio puras: `cartao_fatura.py` (ciclos e faturas) e `transacao.py` (impacto_no_saldo, recalcular_meta, recalcular_orcamento_mes).
- Todas as rotas de listagem retornam envelope padrao `{ data: [...], meta: { page, page_size, total, total_pages, has_next } }`. Sem excecoes ativas.
- `app/crud/` ainda existe como legado — nao acrescentar logica nova; migrar para services quando mexer.

### Frontend
- Organizado por dominio em `views/`, com `services/api.ts` centralizando HTTP.
- Chamadas de listagem de recursos nunca devem ser feitas diretamente nas views; todo estado de lista vive em stores Pinia (`src/stores/`).
- Stores cobrem: `auth`, `contas`, `categorias`, `orcamentos`, `metas`, `delegacoes`, `transacoes`.
- `src/services/storage.ts` — unico ponto de acesso ao `localStorage`. Nunca usar `localStorage.*` diretamente.
- `src/services/apiError.ts` — `extractApiError(err, fallback?)` para extrair mensagem legivel de erros Axios.
- Delegacao de acesso existe e usa `X-Act-As-User`; nao remover esse fluxo por acidente.
- Existe logica de cartao/fatura, dizimo automatico, parcelamento, metas e orcamentos; essas regras sao sensiveis.

## Arquivos descendentes
- `backend/CLAUDE.md` contem regras especificas da API, modelos e testes.
- `frontend/CLAUDE.md` contem regras especificas de UI, roteamento, estados e componentes.

## Preferencias locais
- Use `CLAUDE.local.md` para notas pessoais nao versionadas.
- Esse arquivo deve permanecer fora do Git.
