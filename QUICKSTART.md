# Início Rápido

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- PostgreSQL 17+ (14+ funciona; Docker usa 17-alpine)

## 1. Backend

```bash
cd backend

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
cp .env.example .env
```

Edite o `.env` com suas credenciais PostgreSQL:

```env
DATABASE_URL=postgresql://financas_user:financas_pass@localhost:5432/financas_db
SECRET_KEY=sua-chave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

```bash
alembic upgrade head
python seed_categorias.py    # popula 44 categorias padrão
uvicorn app.main:app --reload
```

## 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

`.env` do frontend:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

```bash
npm run dev
```

## 3. Acesse

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs interativos: http://localhost:8000/docs

## Primeiros passos no produto

1. Criar conta em `/registro`
2. Adicionar uma conta em `Contas`
3. Lançar uma transação em `Transações`
4. Ver o dashboard

## Comandos úteis

```bash
# Backend — testes
cd backend
.\venv\Scripts\python.exe -m pytest -q

# Frontend — lint e testes
cd frontend
npm run lint
npm run test
```

## Deploy com Docker

```bash
docker network create app_network
docker volume create financas-project_pgdata
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python seed_categorias.py
```

Para o passo a passo completo com troubleshooting, veja `INSTALACAO.md`.
