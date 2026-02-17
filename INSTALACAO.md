# 🚀 Guia Rápido - Instalação e Seed

## 📋 Passo a Passo Completo

### 1️⃣ Preparar o Ambiente

```bash
# Extrair o boilerplate
tar -xzf financas-cristaos-boilerplate.tar.gz
cd financas-cristaos
```

---

### 2️⃣ Backend - Instalação

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

---

### 3️⃣ Configurar Banco de Dados

**Criar banco PostgreSQL:**
```bash
# Via psql
psql -U postgres
CREATE DATABASE financas_db;
CREATE USER financas_user WITH PASSWORD 'financas_pass';
GRANT ALL PRIVILEGES ON DATABASE financas_db TO financas_user;
\q
```

**Configurar .env:**
```bash
cp .env.example .env
# Editar .env com suas credenciais
```

**`.env` deve conter:**
```env
DATABASE_URL=postgresql://financas_user:financas_pass@localhost:5432/financas_db
SECRET_KEY=sua-chave-secreta-aqui-mude-isso
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ENVIRONMENT=development
```

---

### 4️⃣ Rodar Migrations (Criar Tabelas)

```bash
# Inicializar Alembic (se necessário)
alembic revision --autogenerate -m "initial tables"

# Rodar migrations
alembic upgrade head
```

**Saída esperada:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> xxxx, initial tables
```

---

### 5️⃣ ⭐ POPULAR CATEGORIAS PADRÃO (IMPORTANTE!)

```bash
# Rodar seed de categorias
python seed_categorias.py
```

**Saída esperada:**
```
🌱 Iniciando seed de categorias padrão...
✅ 44 categorias padrão criadas com sucesso!

Resumo:
  📈 Entradas: 6
  📉 Saídas: 37
  🔄 Flexíveis: 1
  📊 Total: 44
```

**⚠️ ATENÇÃO:** Este passo é **OBRIGATÓRIO**! Sem as categorias padrão, os usuários não conseguirão categorizar transações.

---

### 6️⃣ Iniciar Backend

```bash
uvicorn app.main:app --reload
```

**Saída esperada:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Testar:**
```bash
curl http://localhost:8000
# Deve retornar: {"message":"Finanças Cristãs API","status":"online"}
```

---

### 7️⃣ Frontend - Instalação

**Abrir novo terminal:**

```bash
cd frontend

# Instalar dependências
npm install

# Configurar .env
cp .env.example .env
```

**`.env` deve conter:**
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_MODO_CRISTAO=true
```

---

### 8️⃣ Iniciar Frontend

```bash
npm run dev
```

**Saída esperada:**
```
VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## ✅ Verificação

### Backend funcionando?

```bash
# Verificar saúde da API
curl http://localhost:8000/health
# Deve retornar: {"status":"healthy"}

# Verificar categorias padrão
curl http://localhost:8000/api/v1/categorias
# Deve retornar JSON com 44 categorias
```

### Frontend funcionando?

Abrir navegador: http://localhost:5173

Você deve ver:
- Tela inicial com "💰 Finanças Cristãs"
- Botões "Entrar" e "Criar Conta"

---

## 🔧 Comandos Úteis

### Seed de Categorias

```bash
# Listar categorias criadas
python seed_categorias.py --listar

# Recriar categorias (limpa e cria novamente)
python seed_categorias.py
# Responda 's' quando perguntar
```

### Migrations

```bash
# Criar nova migration
alembic revision --autogenerate -m "descrição"

# Aplicar migrations
alembic upgrade head

# Voltar migration
alembic downgrade -1

# Ver histórico
alembic history
```

### Banco de Dados

```bash
# Conectar ao banco
psql -U financas_user -d financas_db

# Listar tabelas
\dt

# Ver categorias padrão
SELECT id, nome, icone, tipo, padrao FROM categorias WHERE padrao = true;

# Contar categorias
SELECT COUNT(*) FROM categorias WHERE padrao = true;
# Deve retornar: 44
```

---

## 📊 Estrutura de Dados Criada

Após rodar migrations + seed:

```
Tabelas criadas:
✅ users
✅ contas
✅ categorias          ← 44 categorias padrão aqui
✅ transacoes
✅ metas
✅ orcamentos
✅ config_cristao
```

**Categorias padrão (44):**
- 6 de entrada (Salário, Freelance, etc)
- 37 de saída (Aluguel, Mercado, Dízimo, etc)
- 1 flexível (Transferência)

---

## ❓ Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'app'"

```bash
# Certifique-se de estar na pasta backend
cd backend
python seed_categorias.py
```

### Erro: "relation 'categorias' does not exist"

```bash
# Rode as migrations primeiro
alembic upgrade head
```

### Erro: "could not connect to server"

```bash
# PostgreSQL não está rodando
# Linux/Mac:
sudo service postgresql start

# Windows:
# Iniciar serviço PostgreSQL pelo Serviços do Windows

# Verificar se está rodando:
psql --version
```

### Erro: "duplicate key value violates unique constraint"

```bash
# Categorias já existem, limpe antes:
python seed_categorias.py
# Responda 's' para recriar
```

### Frontend não conecta ao backend

```bash
# Verificar .env do frontend:
cat frontend/.env
# VITE_API_URL deve ser: http://localhost:8000/api/v1

# Verificar CORS no backend
# Deve permitir http://localhost:5173
```

---

## 📝 Checklist de Instalação

- [ ] Python 3.11+ instalado
- [ ] Node.js 18+ instalado
- [ ] PostgreSQL 14+ instalado e rodando
- [ ] Banco `financas_db` criado
- [ ] Backend: `pip install -r requirements.txt`
- [ ] Backend: `.env` configurado
- [ ] Backend: `alembic upgrade head` executado
- [ ] **Backend: `python seed_categorias.py` executado** ⭐
- [ ] Backend rodando em http://localhost:8000
- [ ] Frontend: `npm install` executado
- [ ] Frontend: `.env` configurado
- [ ] Frontend rodando em http://localhost:5173

---

## 🎯 Próximos Passos

Após instalação:

1. **Criar primeiro usuário:**
   - Acessar http://localhost:5173
   - Clicar em "Criar Conta"
   - Preencher dados

2. **Criar primeira conta:**
   - Ir em "Contas"
   - Adicionar conta (ex: "Carteira")

3. **Criar primeira transação:**
   - Ir em "Transações"
   - Adicionar entrada
   - ☑️ Marcar "Tem Dízimo" (se modo cristão)
   - Ver dízimo criado automaticamente!

4. **Ver dashboard:**
   - Ir em "Dashboard"
   - Ver KPIs e gráficos

---

## 🚀 Pronto!

Seu sistema está rodando com:
- ✅ 44 categorias padrão
- ✅ Sistema de dízimo automático
- ✅ Frontend + Backend integrados
- ✅ Banco de dados configurado

**Dúvidas?** Consulte:
- `FUNCIONAMENTO.md` - Como o sistema funciona
- `ROADMAP.md` - Planejamento de features
- `backend/SEED_CATEGORIAS.md` - Detalhes do seed
