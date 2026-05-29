# Finanças Cristãs

Controle financeiro pessoal com suporte a múltiplas contas, orçamentos, metas e recursos opcionais para cristãos.

## Funcionalidades

### Transações
- Entradas e saídas com categorização
- Parcelamento (2–48x) com rastreamento por parcela
- Despesas fixas e recorrentes
- Duplicar transação com um clique
- Marcação como dízimo automático: flag na entrada gera saída vinculada via UUID

### Contas
- Tipos: carteira, banco, poupança, investimento, cartão de crédito
- Cartão de crédito com ciclo de fatura completo:
  - Fatura atual e fatura fechada separadas
  - Ajuste manual de data de fechamento e vencimento por competência
  - Pagamento de fatura debitando outra conta

### Planejamento
- Orçamentos mensais por categoria com acompanhamento de percentual gasto
- Metas financeiras com valor objetivo e progresso acumulado

### Relatórios
- DRE mensal (Demonstrativo de Resultado): receitas, despesas e resultado por categoria
- Exportação CSV e PDF

### Dashboard
- KPIs: entradas, saídas, saldo do mês, cartão em aberto
- Gráfico de fluxo financeiro (linha/área)
- Despesas por categoria (barras horizontais)
- Orçamento × gasto por categoria (barras de progresso)

### Busca global
- Endpoint `GET /api/v1/busca?q=termo` pesquisa em transações e contas
- Tela `BuscaView` com debounce de 300ms e navegação direta ao resultado

### Colaboração
- Delegação de acesso: compartilhar visão da conta com outro usuário via convite por e-mail
- Impersonação via `X-Act-As-User` no header

### Segurança
- Rate limiting em endpoints de autenticação (slowapi)
- Recuperação de senha via e-mail (`/auth/forgot-password` + `/auth/reset-password`)
- Erros padronizados no formato RFC 7807

## Stack

**Frontend:** Vue 3 + TypeScript + TailwindCSS (tema customizado Forest `#1F5C3A`) + DaisyUI + Pinia + ApexCharts
**Backend:** FastAPI + SQLAlchemy (síncrono) + Alembic + PostgreSQL + JWT
**Infra:** Docker Compose + Nginx + Gunicorn

## Início rápido (desenvolvimento)

Veja `INSTALACAO.md` para o passo a passo completo.

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed_categorias.py
uvicorn app.main:app --reload

# Frontend (novo terminal)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Acesse:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Docs interativos: http://localhost:8000/docs

## Deploy com Docker

```bash
docker compose up -d
```

O `docker-compose.yml` sobe PostgreSQL 17, backend (Gunicorn + Uvicorn workers) e frontend (Nginx servindo o build estático). Veja `INSTALACAO.md` para configuração das variáveis de ambiente de produção.

## Testes

```bash
# Backend — suite completa (pytest + SQLite em memória)
cd backend
.\venv\Scripts\python.exe -m pytest -q

# Frontend — type check
cd frontend
npm run lint

# Frontend — unit tests (Vitest)
npm run test

# Frontend — E2E (Playwright, sobe dev server automaticamente)
npm run test:e2e
```

## CI/CD

Pipeline GitHub Actions em `.github/workflows/ci.yml`, disparado em push e pull request para `main`:

- **backend** — `pytest -q` com SQLite em memória
- **frontend** — `vue-tsc --noEmit` + `vitest run`
- **e2e** — Playwright (Chromium), sobe o dev server via `webServer` no config

## Decisões de arquitetura

| Decisão | Detalhe |
|---|---|
| `AccessContext` | Toda rota protegida usa `AccessContext` de `app/api/deps.py`. Nunca confiar em `user_id` vindo do cliente. |
| Delegação | Usuário pode operar como outro via `X-Act-As-User`. Gerenciado por `AccessContext`. |
| Rate limiting | Endpoints de auth protegidos com slowapi. Desabilitado automaticamente em testes. |
| `storage.ts` | Único ponto de acesso ao `localStorage`. Nunca usar `localStorage.*` diretamente. |
| `apiError.ts` | Helper `extractApiError(err)` para extrair mensagem de erros Axios (suporta Pydantic, string e objeto). |
| Stores Pinia | `useContasStore` e `useCategoriasStore` com deduplicação de fetch — chamadas concorrentes são mescladas. |
| `app/domain/` | Regras de negócio transversais extraídas de `crud_*`. Referência: `domain/cartao_fatura.py`. |

## Documentação

- `INSTALACAO.md` — instalação detalhada com troubleshooting e deploy Docker
- `ESTRUTURA.md` — mapa completo de arquivos
- `backend/README.md` — comandos e configuração do backend
- `backend/README_TESTES.md` — como rodar e entender a suite de testes
- `backend/SEED_CATEGORIAS.md` — seed das 44 categorias padrão
- `ROADMAP.md` — features e melhorias planejadas
- `docs/Plano_Evolucao_Arquitetural_Financas_Project.md` — plano arquitetural detalhado

## Licença

MIT
