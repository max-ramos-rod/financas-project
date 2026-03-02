# Backend Tests Guide

Guia rapido para executar e entender os testes da API.

## Pre-requisitos

- Python 3.12+
- Ambiente virtual criado em `backend/venv`
- Dependencias instaladas com `pip install -r requirements.txt`

## Executar todos os testes

```bash
cd backend
.\venv\Scripts\python.exe -m pytest -q
```

## Executar um arquivo especifico

```bash
cd backend
.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py
```

## Cobertura atual (alto nivel)

- `tests/test_auth.py`
  - login retorna token
  - endpoint protegido exige token valido

- `tests/test_contas_cartao.py`
  - regras de conta cartao de credito
  - saldo forcado para zero no create/update

- `tests/test_contas_fatura.py`
  - `GET /api/v1/contas/{id}/fatura-atual`
  - `POST /api/v1/contas/{id}/pagar-fatura`

- `tests/test_endpoints_smoke.py`
  - smoke CRUD de categorias, metas e orcamentos
  - categoria em uso nao pode ser excluida

- `tests/test_transacoes_cartao_meta_orcamento.py`
  - regras de transacoes com cartao
  - atualizacao de meta e orcamento
  - dizimo automatico (ligar/desligar na edicao)

## Observacoes

- A suite usa banco SQLite em memoria via `tests/conftest.py`.
- Warnings de bibliotecas terceiras podem aparecer e nao impedem o sucesso dos testes.
