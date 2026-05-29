# Backend

## Stack
- FastAPI
- SQLAlchemy sincronico
- Alembic
- PostgreSQL
- Pytest para testes

## Estrutura relevante
- `app/api/v1/endpoints/` rotas HTTP
- `app/api/deps.py` autenticacao, `AccessContext` e delegacao
- `app/core/config.py` — configuracoes da aplicacao (Settings via pydantic-settings)
- `app/core/errors.py` — handlers RFC 7807: `http_exception_handler` (HTTPException → `{type, title, status, detail}`), `validation_exception_handler` (422 Pydantic), `unhandled_exception_handler` (500 generico); todos registrados em `main.py`
- `app/core/limiter.py` — rate limiting via slowapi; endpoints protegidos: `/auth/login` (20/min), `/auth/register` (5/min), `/auth/google` (20/min), `/auth/forgot-password` (3/min), `/auth/reset-password` (5/min)
- `app/core/pagination.py` — `PaginationParams`, `PageMeta`, `PaginationMetaBuilder`
- `app/core/responses.py` — `ResponseEnvelope[T]`, `PaginatedResponseEnvelope[T]`, alias `PagedResponse`; helpers `success_response()` e `paginated_response()`
- `app/core/repositories.py` — `SQLAlchemyRepository[ModelT]` (ABC generico; mutation methods usam `flush()`, nao `commit()`, requer UoW externo)
- `app/contracts/` — Protocol interfaces para todos os repositorios de dominio (`CategoriaRepositoryProtocol`, `ContaRepositoryProtocol`, etc.); definem o contrato que services dependem
- `app/repositories/` — implementacoes concretas: `CategoriaRepository`, `ContaRepository`, `DelegacaoRepository`, `MetaRepository`, `OrcamentoRepository`, `TransacaoRepository`
- `app/services/` — orchestracao de negocio por dominio; services dependem de contracts (injetados via __init__):
  - `transacao.py` — `TransacaoService` (criar, atualizar, excluir; orquestra dizimo, parcelamento, saldo, meta, orcamento)
  - `conta.py` — `ContaService`
  - `categoria.py` — `CategoriaService`
  - `meta.py` — `MetaService`
  - `orcamento.py` — `OrcamentoService`
  - `delegacao.py` — `DelegacaoService`
  - `dizimo.py` — `criar_transacao_dizimo` (funcao, nao classe)
  - `parcelamento.py` — `criar_parcelamento` (funcao, nao classe)
  - `email.py` — `send_password_reset_email`, `send_convite_email` (fallback para log `[DEV]` se SMTP nao configurado)
  - `importacao/` — `detectar_e_parsear` (entry point); parsers para OFX, XLSX, CNAB
- `app/domain/` — regras de dominio puras, sem IO:
  - `cartao_fatura.py` — calculo de ciclos e faturas de cartao
  - `transacao.py` — `impacto_no_saldo`, `normalizar_atraso`, `valor_meta`, `recalcular_meta`, `recalcular_orcamento_mes`, `obter_categoria_dizimo`
- `app/crud/` acesso a dados legado; ainda usado por endpoints nao migrados para services (nao acrescentar logica nova; migrar ao tocar)
- `app/models/` modelos SQLAlchemy (um arquivo por dominio + `enums.py`)
- `app/schemas/` contratos Pydantic

## Padrões arquiteturais atuais

O padrao para novos endpoints e:
```
endpoint -> service -> repository -> db
```

Endpoints legados ainda usam:
```
endpoint -> crud_* -> db
```

Ao modificar um endpoint legado, considere migrá-lo para o padrao com service se o contexto permitir.

Services sao instanciados no topo do modulo do endpoint (ex: `_service = TransacaoService()`). O repositorio concreto e injetado pelo proprio service como default, mas pode ser substituido em testes via `TransacaoService(repo=FakeRepo())`.

## Contrato de resposta padrao

Toda rota de listagem deve retornar `PagedResponse[T]` de `app/core/responses.py`:

```python
from app.core.pagination import PaginationMetaBuilder, PaginationParams
from app.core.responses import PagedResponse

@router.get("/recurso", response_model=PagedResponse[RecursoResponse])
def listar(page: int = 1, page_size: int = 50, ...):
    total = len(items)  # ou query COUNT(*)
    params = PaginationParams(page=page, page_size=page_size)
    return PagedResponse(data=items, meta=PaginationMetaBuilder.build(total, params))
```

Shape da resposta:
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "page_size": 50,
    "total": 123,
    "total_pages": 3,
    "has_next": true
  }
}
```

Recursos sem paginacao real (contas, categorias, orcamentos) retornam todos os itens com `page=1, page_size=max(total,1)`.

Todos os endpoints de listagem retornam `PagedResponse`. Os testes esperam `response.json()["data"]`.

## SQLAlchemyRepository — aviso importante

`app/core/repositories.py` contem `SQLAlchemyRepository` com metodos `create`, `update_fields` e `delete` que usam `db.flush()`, NAO `db.commit()`. O `get_db()` nao faz commit automatico.

Os services concretos em `app/repositories/` herdam de `SQLAlchemyRepository`. O commit e responsabilidade do service (que chama `db.commit()` apos a operacao completa).

Os arquivos `crud_*` existentes NAO devem usar esses metodos de mutacao — eles continuam usando `db.commit()` diretamente.

## Regras de negocio sensiveis
- Transacoes alteram saldo, metas, orcamentos e, em alguns casos, dizimo automatico.
- Cartao de credito tem fluxo proprio de compra, ciclo, fatura e pagamento.
- Entradas em cartao de credito nao sao fluxo normal; respeitar as validacoes existentes.
- Delegacao/impersonacao via `AccessContext` e `X-Act-As-User` deve continuar funcionando.

## Boas praticas obrigatorias
- Toda rota protegida deve usar `AccessContext`, nao confiar em `user_id` vindo do cliente.
- Ao alterar schema de resposta, revisar impacto nos consumers do frontend.
- Ao adicionar coluna/modelo novo, criar migration Alembic; nunca editar migration antiga para reescrever historico.
- Ao mexer em datas de fatura ou competencia, validar cenarios com mes/ano e fechamento real vs previsto.
- Em regras financeiras, prefira testes de API cobrindo o fluxo completo.

## Rate Limiting
- Implementado via `slowapi` em `app/core/limiter.py`.
- Endpoints protegidos: `/auth/login` (20/min), `/auth/register` (5/min), `/auth/forgot-password` (3/min), `/auth/reset-password` (5/min).
- Em testes, o limiter e **desabilitado automaticamente** pelo fixture `disable_rate_limiting` em `conftest.py` (`autouse=True`).
- Para testar rate limiting explicitamente, use o fixture `client_with_limiter` de `tests/test_auth_rate_limiting.py` como referencia.

## Recuperação de Senha
- Fluxo: `POST /auth/forgot-password` → gera token (TTL 1h) → `POST /auth/reset-password` → invalida token.
- Token armazenado em `password_reset_tokens` (model: `app/models/password_reset_token.py`).
- CRUD: `app/crud/crud_password_reset.py` — `criar_token`, `buscar_token_valido`, `marcar_usado`.
- Resposta sempre 200 no forgot-password para nao revelar existencia do e-mail.
- SMTP integrado: `send_password_reset_email` em `app/services/email.py`; se SMTP nao estiver configurado, mantem fallback para log `[DEV]`.

## Importação de Extratos
- Endpoint: `POST /api/v1/importacao/upload` (multipart/form-data: `conta_id` + `file`)
- Limite: 5 MB por arquivo
- Formatos suportados: OFX, XLSX/CSV, CNAB 240/400
- Deteccao automatica de formato via `app/services/importacao/detector.py`
- Resposta: `ImportacaoResult` com `formato_detectado`, `total_no_arquivo`, `importadas`, `duplicatas`, `erros`

## Testes
- Suite completa:
  - `.\venv\Scripts\python.exe -m pytest -q`
- Suites focadas comuns:
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth_password_reset.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth_rate_limiting.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_busca.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/unit/`

## O que evitar
- Nao criar bypass de autenticacao/autorizacao para "facilitar" endpoint.
- Nao recalcular saldo manualmente em endpoint se ja existir fluxo consolidado no dominio/service.
- Nao introduzir SQL raw sem necessidade forte.
- Nao misturar mudanca funcional com refactor amplo em modulo financeiro sem cobertura de testes.
- Nao acrescentar logica de negocio em `crud_*` — usar services.

## Direcao arquitetural
- Fases 0–4 do plano arquitetural concluidas: padronizacao de contracts/responses/errors, service layer, repositories, testes unitarios.
- Proximo passo (Fase 5): migrar endpoints que ainda usam `crud_*` para chamar services. Prioridade: `transacoes.py` (maior volume de logica residual em crud).
- Consulte `docs/Plano_Evolucao_Arquitetural_Financas_Project.md` para o roadmap completo.
- Ruff linting ativo: `python -m ruff check .` passa sem erros; step adicionado ao CI.
