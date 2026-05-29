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
- `app/core/config.py` — configuracoes da aplicacao (settings)
- `app/core/errors.py` — handlers RFC 7807: `http_exception_handler` (HTTPException → `{type, title, status, detail}`), `validation_exception_handler` (422 Pydantic), `unhandled_exception_handler` (500 generico); todos registrados em `main.py`
- `app/core/limiter.py` — rate limiting via slowapi; endpoints protegidos: `/auth/login` (20/min), `/auth/register` (5/min), `/auth/google` (20/min), `/auth/forgot-password` (3/min), `/auth/reset-password` (5/min)
- `app/core/pagination.py` — `PaginationParams`, `PageMeta`, `PaginationMetaBuilder`
- `app/core/responses.py` — `ResponseEnvelope[T]`, `PaginatedResponseEnvelope[T]`, alias `PagedResponse`; helpers `success_response()` e `paginated_response()`
- `app/core/repositories.py` — `SQLAlchemyRepository[ModelT]` (ABC generico; reservado para futura service layer — mutation methods usam `flush()`, nao `commit()`, requer UoW externo)
- `app/crud/` acesso a dados + parte relevante da regra de negocio atual (todos usam `db.commit()` diretamente)
- `app/domain/` regras de dominio extraidas de casos mais complexos
- `app/models/` modelos SQLAlchemy
- `app/schemas/` contratos Pydantic (nota: `schemas/pagination.py` foi removido — usar `app/core/pagination.py`)
- `tests/` cobertura funcional da API

## Padrões arquiteturais atuais
- O padrao predominante hoje e `endpoint -> crud`.
- Parte da regra de negocio ainda esta em `crud_*`; nao espalhar mais sem necessidade.
- Quando a regra ficar muito grande ou transversal, prefira extrair para `app/domain/`.
- `app/domain/cartao_fatura.py` e a referencia atual para calculo de ciclos e faturas de cartao.

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

Por isso, os arquivos `crud_*` existentes NAO devem usar esses metodos de mutacao — eles continuam usando `db.commit()` diretamente. O `SQLAlchemyRepository` e infraestrutura para a futura service layer (onde o commit sera responsabilidade do service).

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
- Em testes, o limiter é **desabilitado automaticamente** pelo fixture `disable_rate_limiting` em `conftest.py` (`autouse=True`).
- Para testar rate limiting explicitamente, use o fixture `client_with_limiter` de `tests/test_auth_rate_limiting.py` como referência.

## Recuperação de Senha
- Fluxo: `POST /auth/forgot-password` → gera token (TTL 1h) → `POST /auth/reset-password` → invalida token.
- Token armazenado em `password_reset_tokens` (model: `app/models/password_reset_token.py`).
- CRUD: `app/crud/crud_password_reset.py` — `criar_token`, `buscar_token_valido`, `marcar_usado`.
- Resposta sempre 200 no forgot-password para não revelar existência do e-mail.
- Integração SMTP pendente — por ora o token é logado em nível INFO (`[DEV]`).

## Testes
- Suite completa:
  - `.\venv\Scripts\python.exe -m pytest -q`
- Suites focadas comuns:
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth_password_reset.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth_rate_limiting.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_transacoes_cartao_meta_orcamento.py`
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_transacoes_filtros.py`

## O que evitar
- Nao criar bypass de autenticacao/autorizacao para "facilitar" endpoint.
- Nao recalcular saldo manualmente em endpoint se ja existir fluxo consolidado no dominio/crud.
- Nao introduzir SQL raw sem necessidade forte.
- Nao misturar mudanca funcional com refactor amplo em modulo financeiro sem cobertura de testes.

## Direcao arquitetural
- Quando possivel, mover logica pesada de `crud_*` para servicos/dominio pequenos e testaveis.
- Padronizacao de responses e erros concluida (Fase 1 do plano arquitetural): `PagedResponse`, RFC 7807, paginacao reutilizavel, rate limiting, recuperacao de senha.
- Proximo passo: criar `TransacaoService` como primeira service layer real, usando `SQLAlchemyRepository` como camada de persistencia.
- Consulte `docs/Plano_Evolucao_Arquitetural_Financas_Project.md` para o roadmap completo.
- SMTP integrado: `send_password_reset_email` em `app/services/email.py`; se SMTP nao estiver configurado, mantém fallback para log `[DEV]`.
- Ruff linting ativo: `python -m ruff check .` passa sem erros; step adicionado ao CI.
