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

Sem SMTP configurado, o convite é criado mas o e-mail automático não é enviado.

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

## Testes

```bash
# Suite completa
.\venv\Scripts\python.exe -m pytest -q

# Arquivo específico
.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py
```

Veja `README_TESTES.md` para o escopo detalhado de cada suite.
