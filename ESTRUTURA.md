# 📁 Estrutura Completa

## Backend

```
backend/
├── app/
│   ├── models/
│   │   ├── user.py              # Model de usuário
│   │   ├── financeiro.py        # DÍZIMO AUTOMÁTICO
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py            # Configurações
│   │   └── security.py          # JWT + Bcrypt
│   ├── db/
│   │   └── session.py           # SQLAlchemy
│   ├── api/v1/endpoints/        # Rotas (criar)
│   ├── schemas/                 # Pydantic (criar)
│   ├── crud/                    # DB ops (criar)
│   └── main.py                  # FastAPI app
├── alembic/
│   ├── env.py                   # Config migrations
│   └── versions/                # Migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Frontend

```
frontend/
├── src/
│   ├── views/
│   │   ├── HomeView.vue
│   │   ├── LoginView.vue
│   │   └── DashboardView.vue
│   ├── stores/
│   │   └── auth.ts              # Pinia
│   ├── services/
│   │   └── api.ts               # Axios
│   ├── types/
│   │   └── index.ts             # TypeScript
│   ├── router/
│   │   └── index.ts             # Vue Router
│   ├── assets/
│   │   └── style.css            # Tailwind
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── index.html
```

## Models Principais

### Transacao (com Dízimo)
- `tem_dizimo`: Boolean
- `percentual_dizimo`: Float
- `transacao_dizimo_uuid`: String
- `e_dizimo`: Boolean
- `entrada_origem_id`: Integer

### Conta
- Carteira, Banco, Poupança, etc

### Categoria
- 30+ categorias pré-definidas
- Customizáveis por usuário

### Meta
- Objetivos financeiros

### Orcamento
- Limite mensal por categoria
