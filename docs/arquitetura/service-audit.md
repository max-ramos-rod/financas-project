# Inventário de Serviços — Estado Atual

**Gerado em**: 2026-05-29  
**Base de avaliação**: código em `backend/app/`

---

## Classificação

### ✅ Já extraído (completo, puro, testável isoladamente)

| Módulo | Localização | O que faz | Dependência de DB |
|---|---|---|---|
| `valor_efetivo_transacao` | `domain/cartao_fatura.py` | Calcula valor real (multa/juros/desconto) | Não |
| `calcular_periodo_fatura` | `domain/cartao_fatura.py` | Período do ciclo de fechamento | Não |
| `calcular_vencimento_fatura` | `domain/cartao_fatura.py` | Data de vencimento da fatura | Não |
| `impacto_no_saldo` | `domain/transacao.py` | Impacto financeiro de uma transação | Não |
| `normalizar_atraso` | `domain/transacao.py` | Marca ATRASADO em memória | Não |
| `valor_meta` | `domain/transacao.py` | Valor de contribuição para meta | Não |
| `send_password_reset_email` | `services/email.py` | Envio SMTP de reset de senha | Não |
| `send_invitation_email` | `services/email.py` | Envio SMTP de convite de delegação | Não |
| `detectar_e_parsear` | `services/importacao/` | Parser de CSV/CNAB/OFX | Não |

---

### ⚠️ Parcialmente extraído (mistura lógica pura com acesso ao banco)

| Módulo | Localização | Problema |
|---|---|---|
| `recalcular_meta` | `domain/transacao.py` | Função de domínio, mas acessa `db.query(Meta)` diretamente |
| `recalcular_orcamento_mes` | `domain/transacao.py` | Idem — `db.query(Orcamento)` + `db.query(Transacao)` |
| `obter_categoria_dizimo` | `domain/transacao.py` | Busca + criação no DB dentro do domínio |
| `obter_resumo_fatura_por_competencia` | `domain/cartao_fatura.py` | Cálculo puro mas faz `db.query(Transacao)` |
| `TransacaoService` | `services/transacao.py` | Orquestração correta, mas sem Protocol → não testável sem DB |

---

### ❌ Ainda acoplado (regra de negócio dentro de crud)

| Módulo | Localização | O que está acoplado |
|---|---|---|
| `get_transacoes` | `crud/crud_transacao.py` | Filtro de orçamento faz queries adicionais ao DB |
| `crud_conta.py` | `crud/crud_conta.py` | Validações de tipo de conta mescladas com persistência |
| `crud_meta.py` | `crud/crud_meta.py` | Regras de meta (valor_alvo, prazo) dentro do crud |
| `crud_orcamento.py` | `crud/crud_orcamento.py` | Idem |
| `crud_categoria.py` | `crud/crud_categoria.py` | Validação de duplicidade por nome/tipo no crud (nível aceitável) |
| `crud_delegacao.py` | `crud/crud_delegacao.py` | Geração de token, expiração, validação no crud |

---

### 🔲 Não implementado (identificado no roadmap)

| Funcionalidade | Fase | Pré-requisito |
|---|---|---|
| `repositories/` — pasta dedicada com implementações concretas | Fase 4 | — |
| `contracts/` — Protocols para repositórios | Fase 5 | Fase 4 |
| Testes unitários (sem DB) | Fase 6 | Fase 5 (Protocols) |
| Transferência entre contas | Fase 3 | Fase 5 + Fase 6 |
| Extração de `criar_parcelamento` como use case | Fase 3 | Fase 5 + Fase 6 |
| Extração de `aplicar_dizimo` como use case | Fase 3 | Fase 5 + Fase 6 |
| Logs estruturados / correlation-id | Fase 12 | — |

---

## Recomendação de Ordem de Execução

```
Fase 4 → Fase 5 → Fase 6 → Fase 3 → (Fase 7 ampliada) → Fases 8-10 → Fase 12
```

**Por que não inverter Fase 3 e 5:**

`TransacaoService.criar` tem 3 ramos complexos:
- parcelamento (loop + flush + recalculos)
- dízimo (flush para ID + criação do par)
- transação simples

Extrair esses ramos como `create_installments` / `apply_tithe` sem Protocols (Fase 5)
não agrega testabilidade — apenas reorganiza código. O risco de regressão supera
o benefício. A ordem correta é: criar Protocols → criar unit tests com mocks →
então refatorar com confiança.

---

## Métricas Atuais

| Métrica | Valor |
|---|---|
| Testes de integração | 90 passando |
| Testes unitários (sem DB) | 0 |
| Cobertura de regras financeiras críticas | ~75% (integração) |
| Funções puras no domínio | 5 |
| Funções de domínio com acesso a DB | 3 |
| Services com Protocol | 0 |
