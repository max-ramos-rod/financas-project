# Guia de Instalação

## Pré-requisitos

- Python 3.12+
- Node.js 20+
- PostgreSQL 17+ (recomendado; 14+ funciona mas o Docker usa 17-alpine)

---

## Instalação para desenvolvimento

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd financas-project
```

### 2. Backend

```bash
cd backend

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 3. Banco de dados

```bash
# Via psql
psql -U postgres
CREATE DATABASE financas_db;
CREATE USER financas_user WITH PASSWORD 'financas_pass';
GRANT ALL PRIVILEGES ON DATABASE financas_db TO financas_user;
\q
```

Configurar `.env`:

```bash
cp .env.example .env
```

Variáveis obrigatórias:

```env
DATABASE_URL=postgresql://financas_user:financas_pass@localhost:5432/financas_db
SECRET_KEY=sua-chave-secreta-aqui-mude-isso
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ENVIRONMENT=development
```

Variáveis opcionais (sessão e e-mail):

```env
SESSION_INACTIVITY_MINUTES=30       # expirar sessão por inatividade (padrão 2)
SESSION_REFRESH_THRESHOLD_SECONDS=300
FRONTEND_URL=http://localhost:5173  # usado nos links de convite
SMTP_HOST=smtp.example.com          # sem SMTP, convites são criados sem e-mail
```

### 4. Migrations

```bash
alembic upgrade head
```

### 5. Seed de categorias (obrigatório)

```bash
python seed_categorias.py
```

Popula 44 categorias padrão. Sem este passo os usuários não conseguem categorizar transações. Veja `SEED_CATEGORIAS.md` para detalhes.

### 6. Iniciar backend

```bash
uvicorn app.main:app --reload
```

Verificar: `curl http://localhost:8000/health` → `{"status":"healthy"}`

### 7. Frontend

Novo terminal:

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

Acesse http://localhost:5173.

---

## Deploy com Docker Compose

O projeto inclui Dockerfiles para backend e frontend e um `docker-compose.yml` pronto.

### Estrutura dos containers

| Container | Imagem | Porta |
|---|---|---|
| `financas_ibf_db` | postgres:17-alpine | interna |
| `financas_backend` | build local (Gunicorn + 2 workers) | 8000 (interna) |
| `financas_frontend` | build multi-stage Node → Nginx | 5173:80 |

### Configurar variáveis de produção

```bash
# Backend
cp backend/.env.example backend/.env
# Editar com credenciais de produção

# Banco (arquivo separado para o container db)
# backend/.env.confdb deve conter:
# POSTGRES_USER=...
# POSTGRES_PASSWORD=...
# POSTGRES_DB=financas_db
```

### Volumes e networks externos

```bash
docker network create app_network
docker volume create financas-project_pgdata
```

### Subir

```bash
docker compose up -d
```

### Primeira execução — migrations e seed

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python seed_categorias.py
```

---

## Convites por e-mail (opcional)

Configure no `.env` do backend:

```env
FRONTEND_URL=http://localhost:5173
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=no-reply@example.com
SMTP_PASSWORD=sua-senha
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=no-reply@example.com
```

Sem SMTP configurado, o convite é criado normalmente — o e-mail automático não é enviado.

---

## Checklist de instalação (desenvolvimento)

- [ ] Python 3.12+ instalado
- [ ] Node.js 20+ instalado
- [ ] PostgreSQL 14+ rodando
- [ ] Banco `financas_db` criado
- [ ] `pip install -r requirements.txt` executado
- [ ] `.env` do backend configurado
- [ ] `alembic upgrade head` executado
- [ ] `python seed_categorias.py` executado
- [ ] Backend rodando em http://localhost:8000
- [ ] `npm install` executado
- [ ] `.env` do frontend configurado
- [ ] Frontend rodando em http://localhost:5173

---

## Troubleshooting

### ModuleNotFoundError: No module named 'app'

```bash
cd backend
python seed_categorias.py
```

### relation 'categorias' does not exist

```bash
alembic upgrade head
```

### could not connect to server

```bash
# Linux/Mac:
sudo service postgresql start
# Windows: iniciar serviço PostgreSQL pelo Gerenciador de Serviços
```

### Frontend não conecta ao backend

Verificar `frontend/.env` — `VITE_API_URL` deve ser `http://localhost:8000/api/v1`.

### duplicate key value violates unique constraint

```bash
python seed_categorias.py
# Responda 's' para recriar
```
