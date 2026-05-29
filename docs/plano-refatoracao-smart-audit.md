# Plano de Refatoração: Smart-Audit → Financas-Project

**Versão base**: `financas-project @ v1.0.0`  
**Referência**: `C:\Projetos\smart-audit`  
**Data**: 2026-05-28  
**Executor**: Agente Orquestrador com sub-agentes especializados

---

## Visão Geral

O smart-audit é uma plataforma SaaS de auditorias com padrões de engenharia maduros que podem ser portados incrementalmente para o financas-project. O mapeamento abaixo identifica o que é aproveitável, o que precisa de adaptação e o que deve ser ignorado (fora de domínio).

### O que será portado

| # | Funcionalidade | Origem (smart-audit) | Destino (financas) | Prioridade |
|---|---|---|---|---|
| 1 | Recuperação de senha (forgot/reset) | `backend/app/modules/auth/` + 4 views | `backend/app/api/v1/endpoints/auth.py` + 2 views | 🔴 Alta |
| 2 | Rate limiting com slowapi | `app/core/limiter.py` | `backend/app/core/` | 🔴 Alta |
| 3 | Respostas de erro RFC 7807 | `app/core/errors.py` | `backend/app/core/` | 🔴 Alta |
| 4 | Health check endpoint | `app/api/v1/router.py` | `backend/app/api/v1/` | 🟡 Média |
| 5 | CI/CD GitHub Actions | `.github/workflows/ci.yml` | `.github/workflows/` | 🟡 Média |
| 6 | Ruff linting (Python) | `pyproject.toml` | `backend/pyproject.toml` ou `backend/` | 🟡 Média |
| 7 | Abstração de localStorage | `services/api/storage.ts` | `frontend/src/services/` | 🟡 Média |
| 8 | Parser de erros RFC 7807 | `services/api/problem.ts` | `frontend/src/services/` | 🟡 Média |
| 9 | Busca full-text (transações) | `app/modules/search/` + `SearchView.vue` | backend endpoint + frontend view | 🟡 Média |
| 10 | Playwright E2E tests | `frontend/e2e/` + `playwright.config.ts` | `frontend/` | 🟡 Média |
| 11 | Export PDF de fatura | `app/modules/submissions/service.py` | `backend/app/domain/cartao_fatura.py` | 🟢 Baixa |
| 12 | Export CSV de transações | `app/modules/submissions/service.py` | `backend/app/api/v1/endpoints/transacoes.py` | 🟢 Baixa |

### O que NÃO será portado

- Formulários versionados (fora de domínio)
- Inspeções / Submissions (fora de domínio)
- Teams / Memberships (financas tem delegação própria via X-Act-As-User)
- SQLAlchemy async (refactor invasivo, não justificado no momento)
- radix-vue (financas usa DaisyUI — manter consistência)

---

## Arquitetura do Orquestrador

```
OrchestratorAgent
│
├── BackendAgent       → FastAPI, SQLAlchemy, Python, pytest
├── FrontendAgent      → Vue 3, TypeScript, Pinia, DaisyUI
├── TestAgent          → pytest integration, Vitest unit, Playwright E2E
└── DocumentationAgent → CLAUDE.md, README, comentários de código
```

### Regras de orquestração

1. Cada fase tem pré-requisitos explícitos — o orquestrador deve aguardar conclusão antes de avançar
2. Backend e Frontend de uma mesma fase **podem rodar em paralelo** quando não há dependência de contrato de API
3. TestAgent sempre roda **após** a fase de implementação correspondente
4. DocumentationAgent roda **no final de cada fase**
5. Critério de conclusão de fase: todos os testes passando + vue-tsc clean + lint clean

---

## FASE 1 — Infraestrutura de Segurança e Qualidade

> **Pré-requisito**: nenhum  
> **Paralelismo**: BackendAgent + FrontendAgent podem rodar simultâneos  
> **Entregáveis**: rate limiting ativo, erros RFC 7807, recuperação de senha, localStorage abstraído

---

### FASE 1 — BackendAgent

#### Tarefa 1.B.1 — Rate Limiting

**Fonte**: `C:\Projetos\smart-audit\backend\app\core\limiter.py`

**Objetivo**: Adicionar slowapi ao financas-project para proteger endpoints sensíveis.

**Passos**:
1. Adicionar `slowapi>=0.1.9` ao `backend/requirements.txt` ou equivalente
2. Criar `backend/app/core/limiter.py` copiando a estrutura do smart-audit:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   limiter = Limiter(key_func=get_remote_address)
   ```
3. Registrar o limiter no `backend/app/main.py` (middleware + exception handler)
4. Aplicar decorators nos endpoints sensíveis:
   - `POST /auth/login` → `@limiter.limit("10/minute")`
   - `POST /auth/register` → `@limiter.limit("5/minute")`
   - `POST /auth/google` → `@limiter.limit("10/minute")`
   - `POST /auth/forgot-password` → `@limiter.limit("3/minute")`
5. Em testes: desabilitar limiter em `conftest.py` via override do app state

**Arquivos alterados**:
- `backend/requirements.txt` (add slowapi)
- `backend/app/core/limiter.py` (novo)
- `backend/app/main.py` (registrar middleware)
- `backend/app/api/v1/endpoints/auth.py` (decorators)

**Validação**: `.\venv\Scripts\python.exe -m pytest -q tests/test_auth.py`

---

#### Tarefa 1.B.2 — RFC 7807 Error Responses

**Fonte**: `C:\Projetos\smart-audit\backend\app\core\errors.py`

**Objetivo**: Padronizar respostas de erro com `type`, `title`, `status`, `detail` em vez de `{"detail": "string"}` puro.

**Passos**:
1. Criar `backend/app/core/errors.py` com handler para `HTTPException` e `RequestValidationError`:
   ```python
   def http_exception_handler(request, exc):
       return JSONResponse(
           status_code=exc.status_code,
           content={"type": "about:blank", "title": ..., "status": exc.status_code, "detail": exc.detail}
       )
   ```
2. Registrar handlers em `backend/app/main.py`:
   ```python
   app.add_exception_handler(HTTPException, http_exception_handler)
   app.add_exception_handler(RequestValidationError, validation_exception_handler)
   ```
3. Manter compatibilidade: o campo `detail` ainda é retornado para não quebrar o frontend existente

**Arquivos alterados**:
- `backend/app/core/errors.py` (novo)
- `backend/app/main.py` (registrar handlers)

**Atenção**: Verificar se o frontend lê `err?.response?.data?.detail` — deve continuar funcionando após a mudança.

**Validação**: `.\venv\Scripts\python.exe -m pytest -q` (suite completa)

---

#### Tarefa 1.B.3 — Recuperação de Senha

**Fonte**: `C:\Projetos\smart-audit\backend\app\modules\auth\service.py` (métodos `forgot_password`, `reset_password`)

**Objetivo**: Implementar endpoints `POST /auth/forgot-password` e `POST /auth/reset-password`.

**Passos**:

1. **Migration Alembic**: Criar tabela `password_reset_tokens`:
   ```sql
   CREATE TABLE password_reset_tokens (
     id SERIAL PRIMARY KEY,
     user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
     token VARCHAR(64) NOT NULL UNIQUE,
     expires_at TIMESTAMP NOT NULL,
     used_at TIMESTAMP,
     created_at TIMESTAMP DEFAULT now()
   );
   CREATE INDEX ix_password_reset_tokens_token ON password_reset_tokens(token);
   ```
   Rodar: `alembic revision --autogenerate -m "add_password_reset_tokens"` e `alembic upgrade head`

2. **Model SQLAlchemy**: Criar `backend/app/models/password_reset_token.py`

3. **Schema Pydantic**: Em `backend/app/schemas/auth.py` adicionar:
   - `ForgotPasswordRequest(email: str)`
   - `ResetPasswordRequest(token: str, password: str)`
   - `ForgotPasswordResponse(message: str)`

4. **CRUD**: Criar `backend/app/crud/crud_password_reset.py`:
   - `criar_token(db, user_id)` → gera token `secrets.token_urlsafe(32)`, TTL 1h
   - `buscar_token_valido(db, token)` → retorna se existe, não expirado, não usado
   - `marcar_usado(db, token_obj)`
   - `limpar_tokens_expirados(db, user_id)` → cleanup preventivo

5. **Endpoints** em `backend/app/api/v1/endpoints/auth.py`:
   ```python
   @router.post("/forgot-password")
   async def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
       user = crud_usuario.buscar_por_email(db, body.email)
       if user:  # resposta sempre 200 para não revelar existência
           token_obj = crud_password_reset.criar_token(db, user.id)
           # TODO: integrar SMTP — por ora, logar o token em dev
           logger.info(f"[DEV] password reset token: {token_obj.token}")
       return {"message": "Se o e-mail existir, você receberá o link em breve."}

   @router.post("/reset-password")
   async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
       token_obj = crud_password_reset.buscar_token_valido(db, body.token)
       if not token_obj:
           raise HTTPException(400, "Token inválido ou expirado.")
       user = crud_usuario.buscar_por_id(db, token_obj.user_id)
       crud_usuario.atualizar_senha(db, user, body.password)
       crud_password_reset.marcar_usado(db, token_obj)
       return {"message": "Senha alterada com sucesso."}
   ```

6. Aplicar `@limiter.limit("3/minute")` nos dois endpoints (depende da Tarefa 1.B.1)

**Arquivos novos/alterados**:
- `backend/alembic/versions/xxxx_add_password_reset_tokens.py` (migration)
- `backend/app/models/password_reset_token.py` (novo)
- `backend/app/schemas/auth.py` (adicionar schemas)
- `backend/app/crud/crud_password_reset.py` (novo)
- `backend/app/api/v1/endpoints/auth.py` (2 novos endpoints)

**Validação**: `.\venv\Scripts\python.exe -m pytest -q tests/test_auth.py`

---

#### Tarefa 1.B.4 — Health Check

**Fonte**: smart-audit `/health` endpoint

**Objetivo**: Endpoint simples para monitoramento e docker-compose healthcheck.

**Passos**:
1. Adicionar em `backend/app/main.py` ou em roteador separado:
   ```python
   @app.get("/health", tags=["infra"])
   def health():
       return {"status": "ok"}
   ```
2. Atualizar `docker-compose.yml` healthcheck do backend:
   ```yaml
   healthcheck:
     test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
   ```

**Arquivos alterados**: `backend/app/main.py`, `docker-compose.yml`

---

#### Tarefa 1.B.5 — Ruff Linting

**Fonte**: `C:\Projetos\smart-audit\pyproject.toml` (seção `[tool.ruff]`)

**Objetivo**: Substituir ou complementar o linter atual com ruff para consistência.

**Passos**:
1. Verificar se financas usa flake8/pylint atualmente: `ls backend/`
2. Criar ou atualizar `backend/pyproject.toml` com configuração ruff:
   ```toml
   [tool.ruff]
   line-length = 120
   select = ["E", "F", "W", "I"]
   ignore = ["E501"]

   [tool.ruff.isort]
   known-first-party = ["app"]
   ```
3. Adicionar script npm/Makefile: `ruff check backend/`
4. Corrigir warnings existentes no código (rodar `ruff check --fix backend/`)

**Validação**: `ruff check backend/` sem erros

---

### FASE 1 — FrontendAgent

#### Tarefa 1.F.1 — Abstração de localStorage

**Fonte**: `C:\Projetos\smart-audit\frontend\src\services\api\storage.ts`

**Objetivo**: Centralizar leitura/escrita do localStorage em vez de acessos diretos espalhados.

**Passos**:
1. Criar `frontend/src/services/storage.ts`:
   ```typescript
   const KEYS = {
     token: 'financas_token',
     user: 'financas_user',
     theme: 'financas_theme',
     importHistory: 'financas_import_history',
   } as const

   export const storage = {
     getToken: () => localStorage.getItem(KEYS.token),
     setToken: (v: string) => localStorage.setItem(KEYS.token, v),
     removeToken: () => localStorage.removeItem(KEYS.token),
     getUser: () => { try { return JSON.parse(localStorage.getItem(KEYS.user) ?? 'null') } catch { return null } },
     setUser: (v: unknown) => localStorage.setItem(KEYS.user, JSON.stringify(v)),
     removeUser: () => localStorage.removeItem(KEYS.user),
     getImportHistory: (): string[] => { try { return JSON.parse(localStorage.getItem(KEYS.importHistory) ?? '[]') } catch { return [] } },
     setImportHistory: (v: string[]) => localStorage.setItem(KEYS.importHistory, JSON.stringify(v)),
     clear: () => Object.values(KEYS).forEach(k => localStorage.removeItem(k)),
   }
   ```
2. Substituir todos `localStorage.getItem/setItem` nas stores e views por `storage.*`
   - `frontend/src/stores/auth.ts`
   - `frontend/src/views/Transacoes/ImportacaoView.vue`
3. Manter retrocompatibilidade: as keys existentes devem ser as mesmas usadas atualmente

**Arquivos novos/alterados**:
- `frontend/src/services/storage.ts` (novo)
- `frontend/src/stores/auth.ts` (substituir acesso direto)
- `frontend/src/views/Transacoes/ImportacaoView.vue` (substituir acesso direto)

**Validação**: `npm run lint` + `npm run test`

---

#### Tarefa 1.F.2 — Parser de Erros RFC 7807

**Fonte**: `C:\Projetos\smart-audit\frontend\src\services\api\problem.ts`

**Objetivo**: Centralizar extração de mensagem de erro da resposta da API.

**Passos**:
1. Criar `frontend/src/services/apiError.ts`:
   ```typescript
   export function extractApiError(err: unknown): string {
     if (!err || typeof err !== 'object') return 'Erro desconhecido.'
     const axiosErr = err as { response?: { data?: { detail?: unknown } } }
     const detail = axiosErr.response?.data?.detail
     if (typeof detail === 'string') return detail
     if (Array.isArray(detail)) return detail.map(d => d?.msg ?? JSON.stringify(d)).join('; ')
     if (detail && typeof detail === 'object' && 'msg' in detail) return String((detail as {msg:string}).msg)
     return 'Ocorreu um erro. Tente novamente.'
   }
   ```
2. Substituir padrões `err?.response?.data?.detail || 'Erro...'` pelo helper em todas as views
   - Verificar via grep: `grep -r "response?.data?.detail" frontend/src/views/`
3. Manter o mesmo comportamento — só centraliza o padrão

**Arquivos novos/alterados**:
- `frontend/src/services/apiError.ts` (novo)
- Views com extração manual de erro (substituir progressivamente)

**Validação**: `npm run lint` + `npm run test`

---

#### Tarefa 1.F.3 — Telas de Recuperação de Senha

**Fonte**: `C:\Projetos\smart-audit\frontend\src\views\auth\ForgotPasswordView.vue` e `ResetPasswordView.vue`

**Pré-requisito**: Tarefa 1.B.3 concluída (endpoints no backend)

**Objetivo**: Implementar as telas de recuperação de senha seguindo o design system atual do financas-project.

**Passos**:

1. **ForgotPasswordView** — Criar `frontend/src/views/Auth/ForgotPasswordView.vue`:
   - Layout idêntico ao LoginView (header público + Lockup + footer inline)
   - Formulário: campo e-mail + botão "Enviar link"
   - Estado: `loading`, `error`, `enviado` (boolean para mostrar mensagem de sucesso)
   - Sucesso: mostrar mensagem "Se o e-mail existir, você receberá o link em breve." sem revelar existência
   - Chamar `POST /auth/forgot-password` via `api.post()`
   - Link "Voltar para login" abaixo do formulário

2. **ResetPasswordView** — Criar `frontend/src/views/Auth/ResetPasswordView.vue`:
   - Layout idêntico
   - Ler `?token=` da query string via `route.query.token`
   - Formulário: nova senha + confirmar senha (com toggle mostrar/ocultar, igual ao RegistroView)
   - Validar senhas iguais no client antes de enviar
   - Chamar `POST /auth/reset-password` com `{ token, password }`
   - Sucesso: redirecionar para `/login` com mensagem "Senha alterada. Faça login."
   - Erro de token inválido/expirado: mostrar `alert-error` claro

3. **Router** — Adicionar em `frontend/src/router/index.ts`:
   ```typescript
   { path: '/recuperar-senha', name: 'recuperar-senha', component: () => import('@/views/Auth/ForgotPasswordView.vue'), meta: { public: true } },
   { path: '/redefinir-senha', name: 'redefinir-senha', component: () => import('@/views/Auth/ResetPasswordView.vue'), meta: { public: true } },
   ```

4. **LoginView** — Substituir `<a href="#">Esqueci a senha</a>` por:
   ```html
   <router-link to="/recuperar-senha" class="text-primary font-medium hover:underline">Esqueci a senha</router-link>
   ```

**Arquivos novos/alterados**:
- `frontend/src/views/Auth/ForgotPasswordView.vue` (novo)
- `frontend/src/views/Auth/ResetPasswordView.vue` (novo)
- `frontend/src/router/index.ts` (2 novas rotas)
- `frontend/src/views/Auth/LoginView.vue` (trocar href por router-link)

**Validação**: `npm run lint` + testar fluxo completo no browser

---

### FASE 1 — TestAgent

#### Tarefa 1.T.1 — Testes de Rate Limiting

**Arquivo**: `backend/tests/test_auth.py` (adicionar casos)

- `test_login_rate_limit`: 11 POSTs seguidos para `/auth/login` → 11º retorna 429
- `test_forgot_password_rate_limit`: 4 POSTs → 4º retorna 429
- Usar fixture para desabilitar limiter em outros testes (via `app.state.limiter.enabled = False`)

---

#### Tarefa 1.T.2 — Testes de Recuperação de Senha

**Arquivo novo**: `backend/tests/test_auth_password_reset.py`

Casos obrigatórios:
- `test_forgot_password_email_existente` → 200 + mensagem genérica
- `test_forgot_password_email_inexistente` → 200 + mesma mensagem genérica (não revelar)
- `test_reset_password_token_valido` → 200 + senha alterada
- `test_reset_password_token_expirado` → 400
- `test_reset_password_token_ja_usado` → 400
- `test_reset_password_token_invalido` → 400
- `test_login_apos_reset` → fluxo completo: forgot → reset → login com nova senha

---

#### Tarefa 1.T.3 — Testes Vitest para Storage e apiError

**Arquivo novo**: `frontend/src/__tests__/storage.test.ts`
- Testa get/set/remove de cada key
- Testa `clear()` apaga todas as keys

**Arquivo novo**: `frontend/src/__tests__/apiError.test.ts`
- Testa string detail, array detail, objeto detail, erro sem response

---

### FASE 1 — DocumentationAgent

#### Tarefa 1.D.1 — Atualizar CLAUDE.md

**Arquivo**: `backend/CLAUDE.md`
- Adicionar seção "Rate Limiting": como desabilitar em testes, endpoints protegidos
- Adicionar seção "Recuperação de Senha": fluxo, modelo, TTL, nota sobre SMTP

**Arquivo**: `frontend/CLAUDE.md`
- Adicionar: `storage.ts` como única fonte de acesso ao localStorage
- Adicionar: `apiError.ts` como helper de extração de erro

---

## FASE 2 — Busca e Observabilidade

> **Pré-requisito**: Fase 1 concluída  
> **Paralelismo**: Backend + Frontend em paralelo até integração final

---

### FASE 2 — BackendAgent

#### Tarefa 2.B.1 — Endpoint de Busca Full-Text

**Fonte**: `C:\Projetos\smart-audit\backend\app\modules\search\`

**Objetivo**: Endpoint `GET /busca?q=<termo>` que pesquisa em transações e contas.

**Passos**:
1. Criar `backend/app/api/v1/endpoints/busca.py`:
   ```python
   @router.get("/busca")
   def buscar(q: str = Query(min_length=2, max_length=100), ctx: AccessContext = Depends(...), db: Session = ...):
       # Busca ILIKE em transacoes.descricao e contas.nome
       ...
   ```
2. Resultado: `{ "transacoes": [...], "contas": [...] }` com campos mínimos (id, descricao/nome, valor, data, tipo)
3. Limitar a 10 resultados por tipo, ordenado por `data DESC`
4. Aplicar `@limiter.limit("30/minute")`
5. Registrar rota em `backend/app/api/v1/router.py`

**Validação**: `.\venv\Scripts\python.exe -m pytest -q tests/test_busca.py`

---

#### Tarefa 2.B.2 — Export CSV de Transações

**Fonte**: `C:\Projetos\smart-audit\backend\app\modules\submissions\service.py` (método `export_csv`)

**Objetivo**: Endpoint `GET /transacoes/export?...` que retorna CSV com os mesmos filtros da listagem.

**Passos**:
1. Adicionar em `backend/app/api/v1/endpoints/transacoes.py`:
   ```python
   @router.get("/export")
   def exportar_transacoes(filtros: ..., ctx: AccessContext = Depends(...), db: Session = ...):
       transacoes = crud_transacao.listar_com_filtros(db, ctx.effective_user.id, filtros)
       output = io.StringIO()
       writer = csv.DictWriter(output, fieldnames=["data", "descricao", "valor", "tipo", "status", "conta", "categoria"])
       writer.writeheader()
       for t in transacoes:
           writer.writerow({...})
       return Response(content=output.getvalue(), media_type="text/csv",
           headers={"Content-Disposition": "attachment; filename=transacoes.csv"})
   ```
2. Respeitar todos os filtros existentes (tipo, status, conta, categoria, período)

**Validação**: Teste manual + `.\venv\Scripts\python.exe -m pytest -q tests/test_transacoes_export.py`

---

#### Tarefa 2.B.3 — Export PDF de Fatura

**Fonte**: `C:\Projetos\smart-audit\backend\app\modules\submissions\service.py` (método `export_pdf`)

**Objetivo**: Endpoint `GET /contas/{conta_id}/faturas/{ano}/{mes}/pdf` que retorna PDF da fatura.

**Passos**:
1. Adicionar `fpdf2>=2.8.0` ao `requirements.txt`
2. Criar `backend/app/services/pdf_fatura.py`:
   - Usar fpdf2 para gerar PDF com cabeçalho (nome do cartão, período, vencimento)
   - Tabela de lançamentos (data, descrição, valor, status)
   - Rodapé com totais (total, pago, a pagar)
3. Adicionar endpoint em `backend/app/api/v1/endpoints/contas.py`:
   ```python
   @router.get("/{conta_id}/faturas/{ano}/{mes}/pdf")
   def exportar_fatura_pdf(conta_id: int, ano: int, mes: int, ctx: AccessContext = ..., db: Session = ...):
       fatura = obter_resumo_fatura(db, conta_id, ano, mes, ctx)
       pdf_bytes = gerar_pdf_fatura(fatura)
       return Response(content=pdf_bytes, media_type="application/pdf",
           headers={"Content-Disposition": f"attachment; filename=fatura-{ano}-{mes:02d}.pdf"})
   ```

**Validação**: `.\venv\Scripts\python.exe -m pytest -q tests/test_contas_fatura.py`

---

### FASE 2 — FrontendAgent

#### Tarefa 2.F.1 — SearchView

**Fonte**: `C:\Projetos\smart-audit\frontend\src\views\search\SearchView.vue`

**Objetivo**: Tela de busca global para transações e contas.

**Passos**:
1. Criar `frontend/src/views/Busca/BuscaView.vue`:
   - Layout padrão (container, page header "Busca Global")
   - Input de busca com debounce de 300ms
   - Mínimo 2 caracteres para disparar
   - Seção "Transações" (tabela compacta: data, descrição, valor, conta)
   - Seção "Contas" (lista: nome, tipo, saldo)
   - Cada resultado é clicável → navega para `/transacoes/{id}/editar` ou `/contas/{id}/fatura`
   - Estado vazio: "Digite para buscar" | "Nenhum resultado para '...'"
2. Adicionar rota: `{ path: '/busca', name: 'busca', component: BuscaView }`
3. Adicionar item "Busca" na Navbar/sidebar existente

**Validação**: `npm run lint` + testar no browser com termo existente e inexistente

---

#### Tarefa 2.F.2 — Botão Export CSV na ListaTransacoesView

**Objetivo**: Botão "Exportar CSV" na toolbar da listagem que respeita os filtros ativos.

**Passos**:
1. Em `frontend/src/views/Transacoes/ListaTransacoesView.vue`, adicionar botão ghost na toolbar:
   ```html
   <button class="btn btn-ghost btn-sm sm:btn-md" @click="exportarCSV">Exportar CSV</button>
   ```
2. Handler:
   ```typescript
   const exportarCSV = async () => {
     const params = new URLSearchParams(queryAtualDosFiltros() as Record<string, string>)
     const res = await api.get(`/transacoes/export?${params}`, { responseType: 'blob' })
     const url = URL.createObjectURL(res.data)
     const a = document.createElement('a'); a.href = url; a.download = 'transacoes.csv'; a.click()
     URL.revokeObjectURL(url)
   }
   ```

**Validação**: `npm run lint` + testar download no browser

---

#### Tarefa 2.F.3 — Botão Export PDF na FaturaCartaoView

**Objetivo**: Botão "Exportar PDF" no header da tela de fatura.

**Passos**:
1. Em `frontend/src/views/Contas/FaturaCartaoView.vue`, adicionar botão na área de actions do header:
   ```html
   <button class="btn btn-ghost btn-sm sm:btn-md" @click="exportarPDF" :disabled="!faturaSelecionada">
     Exportar PDF
   </button>
   ```
2. Handler (mesmo padrão do CSV):
   ```typescript
   const exportarPDF = async () => {
     const { ano, mes } = parseCiclo(cicloSelecionado.value)
     const res = await api.get(`/contas/${contaId}/faturas/${ano}/${mes}/pdf`, { responseType: 'blob' })
     const url = URL.createObjectURL(res.data)
     const a = document.createElement('a'); a.href = url; a.download = `fatura-${ano}-${mes.toString().padStart(2,'0')}.pdf`; a.click()
     URL.revokeObjectURL(url)
   }
   ```

**Validação**: `npm run lint` + testar download

---

### FASE 2 — TestAgent

#### Tarefa 2.T.1 — Testes de Busca (Backend)

**Arquivo novo**: `backend/tests/test_busca.py`
- `test_busca_retorna_transacoes`: seed transação com "Mercado" → busca "Mercad" → encontra
- `test_busca_retorna_contas`: seed conta "Nubank" → busca "Nuba" → encontra
- `test_busca_min_chars`: `q=a` → 422
- `test_busca_isolamento`: busca não retorna dados de outro usuário

#### Tarefa 2.T.2 — Playwright E2E Setup

**Fonte**: `C:\Projetos\smart-audit\frontend\playwright.config.ts` + estrutura `e2e/`

**Objetivo**: Configurar Playwright no financas-project com testes de smoke para os fluxos críticos.

**Passos**:
1. Instalar: `npm install -D @playwright/test`
2. Criar `frontend/playwright.config.ts` (adaptar de smart-audit, `baseURL: http://localhost:5173`)
3. Criar `frontend/e2e/` com:
   - `e2e/auth.spec.ts`: login válido, login inválido, recuperação de senha
   - `e2e/transacoes.spec.ts`: listar, criar, editar, excluir
   - `e2e/fatura.spec.ts`: navegar para fatura, mudar ciclo
4. Adicionar scripts em `package.json`:
   ```json
   "test:e2e": "playwright test",
   "test:e2e:ui": "playwright test --ui"
   ```

---

### FASE 2 — DocumentationAgent

#### Tarefa 2.D.1 — CI/CD GitHub Actions

**Fonte**: `C:\Projetos\smart-audit\.github\workflows\ci.yml`

**Objetivo**: Configurar pipeline CI/CD para o financas-project.

**Passos**:
1. Criar `.github/workflows/ci.yml` adaptado:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_USER: financas
          POSTGRES_PASSWORD: financas
          POSTGRES_DB: financas_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - name: Install
        run: cd backend && pip install -r requirements.txt
      - name: Lint
        run: ruff check backend/
      - name: Migrate
        run: cd backend && alembic upgrade head
        env:
          DATABASE_URL: postgresql://financas:financas@localhost:5432/financas_test
      - name: Test
        run: cd backend && python -m pytest -q
        env:
          DATABASE_URL: postgresql://financas:financas@localhost:5432/financas_test

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Install
        run: cd frontend && npm ci
      - name: Type check
        run: cd frontend && npx vue-tsc --noEmit
      - name: Test
        run: cd frontend && npm test
```

**Arquivos novos**:
- `.github/workflows/ci.yml`

#### Tarefa 2.D.2 — Atualizar README e CLAUDE.md

- `README.md`: adicionar seção de endpoints, arquitetura, como rodar
- `CLAUDE.md` raiz: adicionar referência ao plano de refatoração e CI/CD
- `backend/CLAUDE.md`: documentar novos endpoints (busca, export, password reset)
- `frontend/CLAUDE.md`: documentar BuscaView, storage.ts, apiError.ts

---

## Matriz de Dependências

```
Fase 1
  1.B.1 (rate limiting)     ──── nenhum
  1.B.2 (RFC 7807)          ──── nenhum
  1.B.3 (password reset)    ──── depende de 1.B.1 (para decorator)
  1.B.4 (health check)      ──── nenhum
  1.B.5 (ruff)              ──── nenhum
  1.F.1 (storage.ts)        ──── nenhum
  1.F.2 (apiError.ts)       ──── nenhum
  1.F.3 (views senha)       ──── depende de 1.B.3 (endpoints backend)
  1.T.1 (test rate limit)   ──── depende de 1.B.1
  1.T.2 (test pwd reset)    ──── depende de 1.B.3
  1.T.3 (test storage/err)  ──── depende de 1.F.1, 1.F.2
  1.D.1 (docs)              ──── depende de toda a Fase 1

Fase 2 (toda depende de Fase 1 completa)
  2.B.1 (busca backend)     ──── nenhum adicional
  2.B.2 (export csv)        ──── nenhum adicional
  2.B.3 (export pdf)        ──── nenhum adicional
  2.F.1 (BuscaView)         ──── depende de 2.B.1
  2.F.2 (export CSV btn)    ──── depende de 2.B.2
  2.F.3 (export PDF btn)    ──── depende de 2.B.3
  2.T.1 (test busca)        ──── depende de 2.B.1
  2.T.2 (playwright setup)  ──── depende de Fase 1 F.3 concluída
  2.D.1 (CI/CD)             ──── depende de 2.T.2 (playwright)
  2.D.2 (docs gerais)       ──── depende de toda Fase 2
```

---

## Instruções para o Agente Orquestrador

### Prompt inicial sugerido para o orquestrador

```
Você é um agente orquestrador responsável por executar o plano em
docs/plano-refatoracao-smart-audit.md no projeto financas-project.

Execute as fases na ordem. Dentro de cada fase, identifique quais
tarefas são independentes e delegue-as em paralelo para os sub-agentes:

- BackendAgent: tarefas prefixadas com "B" (ex: 1.B.1)
- FrontendAgent: tarefas prefixadas com "F" (ex: 1.F.1)
- TestAgent: tarefas prefixadas com "T" (ex: 1.T.1)
- DocumentationAgent: tarefas prefixadas com "D" (ex: 1.D.1)

Após cada sub-agente concluir, rode a validação descrita na tarefa.
Só avance para a próxima fase quando todos os testes passarem.

Projeto de referência: C:\Projetos\smart-audit
Projeto alvo: C:\Projetos\financas-project
```

### Critério de conclusão global

- `.\venv\Scripts\python.exe -m pytest -q` → todos passando
- `cd frontend && npx vue-tsc --noEmit` → sem erros
- `cd frontend && npm run lint` → sem erros
- `cd frontend && npm test` → todos passando
- `cd frontend && npm run test:e2e` → fluxos críticos passando
- `ruff check backend/` → sem erros

---

## Estimativa de Esforço

| Fase | Tarefas | Complexidade | Estimativa |
|---|---|---|---|
| Fase 1 — Backend | 5 tarefas | Baixa-Média | 3–4h agente |
| Fase 1 — Frontend | 3 tarefas | Baixa | 2–3h agente |
| Fase 1 — Testes | 3 tarefas | Baixa | 1–2h agente |
| Fase 1 — Docs | 1 tarefa | Baixa | 30min agente |
| Fase 2 — Backend | 3 tarefas | Média | 3–4h agente |
| Fase 2 — Frontend | 3 tarefas | Baixa-Média | 2–3h agente |
| Fase 2 — Testes | 2 tarefas | Média | 2–3h agente |
| Fase 2 — Docs/CI | 2 tarefas | Baixa | 1h agente |
| **Total** | **22 tarefas** | | **~14–19h agente** |
