# Backend — Finanças Cristãs API

FastAPI + SQLAlchemy + Alembic + PostgreSQL

## Instalação

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

## Configuração

```bash
cp .env.example .env
```

Variáveis obrigatórias no `.env`:

```env
DATABASE_URL=postgresql://user:pass@localhost:5432/financas_db
SECRET_KEY=sua-chave-secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

Variáveis opcionais:

```env
SESSION_INACTIVITY_MINUTES=30       # expirar sessão por inatividade
SESSION_REFRESH_THRESHOLD_SECONDS=300
FRONTEND_URL=http://localhost:5173  # usado nos links de convite e reset de senha
SMTP_HOST=smtp.example.com          # sem SMTP, e-mails são logados em [DEV]
```

## Migrations

```bash
# Aplicar todas as migrations
alembic upgrade head

# Criar nova migration após alterar models
alembic revision --autogenerate -m "descricao"

# Histórico
alembic history
```

Nunca edite migrations antigas para reescrever histórico.

## Seed de categorias

```bash
python seed_categorias.py
```

Popula 44 categorias padrão (obrigatório na primeira instalação).
Veja `SEED_CATEGORIAS.md` para detalhes.

## Rodar

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs interativos: http://localhost:8000/docs
- Health check: `GET /health` → `{"status": "healthy"}`

## Convites por e-mail (opcional)

Configure no `.env`:

```env
FRONTEND_URL=http://localhost:5173
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=no-reply@example.com
SMTP_PASSWORD=sua-senha
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=no-reply@example.com
```

Sem SMTP configurado, convites e links de recuperação de senha são criados mas o e-mail automático não é enviado (token logado em INFO `[DEV]`).

## Endpoints (prefixo `/api/v1`)

| Prefixo | Destaques |
|---|---|
| `/auth` | login, registro, refresh, `forgot-password`, `reset-password` |
| `/busca` | `GET ?q=` — full-text em transações e contas (mín. 2 chars) |
| `/contas` | CRUD + fatura atual/fechada + ajuste de ciclo + pagar fatura + export PDF |
| `/transacoes` | CRUD + `/visao-financeira` + `/duplicar` + `/export` (CSV) |
| `/relatorios` | `/dre-mensal` + export CSV + export PDF |
| `/importacao` | `POST /upload` — OFX, XLSX, CNAB (≤ 5 MB) |
| `/delegacoes` | invite, accept, revoke, act-as-options, confirm via token |
| `/metas` | CRUD |
| `/orcamentos` | CRUD |
| `/categorias` | CRUD |

## Contrato de resposta

Todos os endpoints de listagem retornam envelope padronizado:

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

Implementado em `app/core/responses.py` (`PagedResponse[T]`) e `app/core/pagination.py` (`PaginationMetaBuilder`).

## Arquitetura

O padrão para novos endpoints é `api → service → repository → db`:
- `app/contracts/` — Protocol interfaces (contratos entre camadas)
- `app/repositories/` — acesso ao banco via `SQLAlchemyRepository`
- `app/services/` — orquestração de negócio por domínio
- `app/domain/` — regras puras sem IO (`cartao_fatura.py`, `transacao.py`)
- `app/crud/` — legado; não acrescentar lógica nova; migrar ao modificar

## Testes

```bash
# Suite completa (integração + unitários)
.\venv\Scripts\python.exe -m pytest -q

# Arquivo específico
.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py

# Somente unitários (sem banco)
.\venv\Scripts\python.exe -m pytest -q tests/unit/
```

Veja `README_TESTES.md` para o escopo detalhado de cada suite.
