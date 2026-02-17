# 🚀 Início Rápido

## Resposta Rápida: App Mobile Grátis?

**SIM! Use PWA:**
- ✅ 100% gratuito
- ✅ Funciona como app
- ✅ Instalável
- ✅ Offline

## Instalação em 3 Passos

### 1. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### 3. Acesse
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Como Funciona o Dízimo

1. Registra entrada com flag "☑ Tem Dízimo"
2. Sistema cria saída automática (10%)
3. Ambas relacionadas via UUID
4. Relatório anual agrupa tudo

## Próximos Passos

1. Criar usuário no /registro
2. Adicionar primeira conta
3. Registrar transação com dízimo
4. Ver dashboard

## Modo Cristão ON/OFF

`.env`:
```
VITE_MODO_CRISTAO=true  # ou false
```
