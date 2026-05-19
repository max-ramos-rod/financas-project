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
- `app/crud/` acesso a dados + parte relevante da regra de negocio atual
- `app/domain/` regras de dominio extraidas de casos mais complexos
- `app/models/` modelos SQLAlchemy
- `app/schemas/` contratos Pydantic
- `tests/` cobertura funcional da API

## Padrões arquiteturais atuais
- O padrao predominante hoje e `endpoint -> crud`.
- Parte da regra de negocio ainda esta em `crud_*`; nao espalhar mais sem necessidade.
- Quando a regra ficar muito grande ou transversal, prefira extrair para `app/domain/`.
- `app/domain/cartao_fatura.py` e a referencia atual para calculo de ciclos e faturas de cartao.

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

## Testes
- Suite completa:
  - `.\venv\Scripts\python.exe -m pytest -q`
- Suites focadas comuns:
  - `.\venv\Scripts\python.exe -m pytest -q tests/test_auth.py`
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
- Padronizacao maior de responses e erros e desejavel, mas deve ser incremental.
