#!/bin/bash
# Script para gerar todos os arquivos do boilerplate

cd "$(dirname "$0")"

echo "🚀 Gerando boilerplate completo..."

# ============ BACKEND ============

# requirements.txt
cat > backend/requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
bcrypt==4.0.1
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
EOF

# .env.example
cat > backend/.env.example << 'EOF'
DATABASE_URL=postgresql://financas_user:financas_pass@localhost:5432/financas_db
SECRET_KEY=change-this-to-a-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ENVIRONMENT=development
EOF

# alembic.ini
cat > backend/alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://financas_user:financas_pass@localhost:5432/financas_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

# backend README
cat > backend/README.md << 'EOF'
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

API: http://localhost:8000
Docs: http://localhost:8000/docs
EOF

# ============ FRONTEND ============

# package.json
cat > frontend/package.json << 'EOF'
{
  "name": "financas-cristaos-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.15",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.5",
    "vee-validate": "^4.12.4",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "typescript": "^5.3.3",
    "vue-tsc": "^1.8.27",
    "vite": "^5.0.11",
    "tailwindcss": "^3.4.1",
    "daisyui": "^4.6.0",
    "autoprefixer": "^10.4.17",
    "postcss": "^8.4.33"
  }
}
EOF

# .env.example
cat > frontend/.env.example << 'EOF'
VITE_API_URL=http://localhost:8000/api/v1
VITE_MODO_CRISTAO=true
EOF

# vite.config.ts
cat > frontend/vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
EOF

# tsconfig.json
cat > frontend/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

# tailwind.config.js
cat > frontend/tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark"],
  },
}
EOF

# postcss.config.js
cat > frontend/postcss.config.js << 'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

# index.html
cat > frontend/index.html << 'EOF'
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Finanças Cristãs</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
EOF

# frontend README
cat > frontend/README.md << 'EOF'
# Frontend - Finanças Cristãs

Vue 3 + TypeScript + TailwindCSS + DaisyUI

## Instalação

```bash
npm install
```

## Configuração

```bash
cp .env.example .env
```

## Desenvolvimento

```bash
npm run dev
```

## Build

```bash
npm run build
```

Frontend: http://localhost:5173
EOF

echo "✅ Boilerplate gerado com sucesso!"
echo ""
echo "📁 Estrutura criada:"
find . -type f -name "*.txt" -o -name "*.json" -o -name "*.md" -o -name "*.ini" -o -name "*.js" -o -name "*.ts" | sort

