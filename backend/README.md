# Backend - Finanças Cristãs API

API FastAPI com PostgreSQL

## Instalação

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuração

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

## Migrations

```bash
alembic upgrade head
```

## Rodar

```bash
uvicorn app.main:app --reload
```

## Convites por E-mail

Configure no `.env`:

```bash
FRONTEND_URL=http://localhost:5173
SMTP_HOST=...
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=no-reply@dominio.com
```

Sem SMTP configurado, o convite e criado mas o envio automatico de e-mail nao ocorre.

API: http://localhost:8000
Docs: http://localhost:8000/docs

## Validação Local (Dia 5)

```bash
# backend
pip install -r requirements.txt
pytest -q
```
