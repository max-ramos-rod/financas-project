# 💰 Finanças Cristãs - Sistema Completo

Controle financeiro pessoal com recursos específicos para cristãos (opcional).

## ✨ Funcionalidades

### Core
- ✅ Entradas e Saídas
- ✅ Múltiplas Contas
- ✅ Empréstimos e Parcelamentos
- ✅ 30+ Categorias
- ✅ Despesas Fixas/Variáveis

### Recursos Cristãos
- ✅ **Dízimo Automático** (flag gera saída)
- ✅ Ofertas e Missões
- ✅ Relatório Anual
- ✅ Cadastro de Igreja

### Avançado
- ✅ Orçamento Mensal
- ✅ Metas Financeiras
- ✅ Dashboard com KPIs
- ✅ Gráficos e Relatórios

## 🚀 Stack

**Frontend:** Vue 3 + TypeScript + TailwindCSS + DaisyUI + Pinia
**Backend:** FastAPI + SQLAlchemy + PostgreSQL + JWT
**Mobile:** PWA (100% gratuito)

## 📱 App Mobile SEM PAGAR Google/Apple

### Opção 1: PWA (Recomendado)
- 100% gratuito
- Instala como app
- Funciona offline

### Opção 2: Lojas Alternativas Gratuitas
- F-Droid (Android)
- Amazon App Store
- APK direto

### Opção 3: Lojas Oficiais (Opcional)
- Google Play: $25 (único)
- Apple Store: $99/ano

## 🛠️ Instalação

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 💡 Sistema de Dízimo Automático

```
Entrada: Salário R$ 3.000 ☑ Dízimo
         ↓ (automático)
Saída: R$ 300 (Dízimo)
```

Relacionados via UUID único.

## 📊 Estrutura

```
financas-cristaos/
├── backend/        # FastAPI
│   ├── app/
│   │   ├── models/     # DÍZIMO AUTOMÁTICO aqui
│   │   ├── api/
│   │   └── core/
│   └── alembic/
├── frontend/       # Vue 3
│   └── src/
└── README.md
```

## 📄 Licença

MIT

## Documentacao complementar

- Backend: `backend/README.md`
- Testes da API: `backend/README_TESTES.md`
