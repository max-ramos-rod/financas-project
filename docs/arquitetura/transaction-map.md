# Mapa de Regras — Transações

**Gerado em**: 2026-05-29  
**Fonte da verdade**: `backend/app/domain/transacao.py`, `backend/app/domain/cartao_fatura.py`, `backend/app/services/transacao.py`

---

## Modelo de Status

```
previsto → liquidado   (baixa manual)
previsto → atrasado    (automático, em memória, sem commit)
previsto → cancelado
liquidado → cancelado
atrasado → liquidado
atrasado → cancelado
```

`normalizar_atraso` (em `domain/transacao.py`): chamada em toda leitura —
PREVISTO + `data_vencimento < hoje` → ATRASADO **em memória** (não persiste).

---

## Fórmulas Financeiras

### valor_efetivo
```
valor_efetivo = max(0, valor + valor_multa + valor_juros - valor_desconto)
```
Fonte: `domain/cartao_fatura.valor_efetivo_transacao`

### impacto_no_saldo
```
if status != LIQUIDADO:  return 0.0
if tipo == ENTRADA:      return +valor_efetivo
if tipo == SAIDA:        return -valor_efetivo
```
Fonte: `domain/transacao.impacto_no_saldo`

### valor_meta
```
if status == CANCELADO:  return 0.0
if tipo == ENTRADA:      return +valor_efetivo
if tipo == SAIDA:        return -valor_efetivo
```
Fonte: `domain/transacao.valor_meta`

---

## Regras de Criação (`TransacaoService.criar`)

### Pré-condições
- `conta_id` deve pertencer ao `user_id` — `ValueError` se não encontrado
- Cartão de crédito + SAÍDA → `status_liquidacao = PREVISTO`, `data_liquidacao = None` (forçado)
- LIQUIDADO sem `data_liquidacao` → `data_liquidacao = data` (auto-preenchido)

### Parcelamento (`parcelado=True` ou `total_parcelas >= 2`)
| Restrição | Erro |
|---|---|
| `total_parcelas < 2` | "Informe a quantidade de parcelas (minimo 2)" |
| `parcelado + recorrente` | "Uma transacao nao pode ser parcelada e recorrente ao mesmo tempo" |
| `parcelado + tem_dizimo + ENTRADA` | "Parcelamento com dizimo automatico nao e suportado" |

**Geração de parcelas:**
- Todas compartilham `grupo_parcelamento_uuid`
- Parcela 1: status conforme solicitado; parcelas 2..N: `PREVISTO`
- `data_parcela_n = _add_months(data_base, n-1)`
- `data_vencimento_n = _add_months(data_vencimento_base, n-1)`
- `valor_multa`, `valor_juros`, `valor_desconto` apenas na parcela 1

**Side effects (parcelamento):**
1. `conta.saldo += impacto_no_saldo(parcela)` para cada parcela
2. `db.flush()` → gera IDs de todas as parcelas
3. `recalcular_meta(db, user_id, meta_id)` para cada meta envolvida
4. `recalcular_orcamento_mes(...)` para cada (categoria, mes, ano) de SAÍDAS
5. `db.commit()`

### Dízimo automático (`tem_dizimo=True` + `tipo=ENTRADA`)
1. `flush()` imediato para gerar `db_transacao.id`
2. Cria SAÍDA: `valor = entrada.valor * (percentual_dizimo / 100)`
3. Categoria: busca "dízimo" do usuário → padrão → cria nova se ausente
4. Campos da SAÍDA: `e_dizimo=True`, `entrada_origem_id=db_transacao.id`, `fixa=True`, `status=PREVISTO`
5. Ambas relacionadas via `transacao_dizimo_uuid` (UUID único)

**Restrição:** dízimo + parcelamento → `ValueError`

### Side effects (transação simples + dízimo)
1. `conta.saldo += impacto_no_saldo(db_transacao)`
2. Se dízimo: `conta.saldo += impacto_no_saldo(dizimo)`
3. `db.flush()`
4. `recalcular_meta` se `meta_id` presente
5. `recalcular_orcamento_mes` para cada (categoria, mes, ano) de SAÍDAS afetadas
6. `db.commit()`
7. `db.refresh(db_transacao)`

---

## Regras de Atualização (`TransacaoService.atualizar`)

### Transação de dízimo (`e_dizimo=True`)
- Apenas `status_liquidacao` e `data_liquidacao` são permitidos
- LIQUIDADO sem `data_liquidacao` → `ValueError`
- Side effect: recalcula impacto no saldo (impacto_novo - impacto_antigo)

### Transação regular
1. Reverte impacto antigo: `conta_antiga.saldo -= impacto_antigo`
2. Aplica impacto novo: `conta_nova.saldo += impacto_novo` (pode ser conta diferente)
3. Cartão crédito + SAÍDA → força `PREVISTO` mesmo no update
4. LIQUIDADO sem `data_liquidacao` → `ValueError`

### Gerenciamento do dízimo no update
| Estado antes | Estado depois | Ação |
|---|---|---|
| tinha dízimo | continua com dízimo | atualiza valor, data, conta, descrição do dízimo |
| tinha dízimo | removeu dízimo | apaga dízimo, reverte saldo do dízimo |
| não tinha dízimo | adicionou dízimo | cria novo dízimo |
| não tinha dízimo | continua sem dízimo | nenhuma ação |

**Side effects:**
1. `db.flush()`
2. `recalcular_meta` para meta antiga e nova (se diferentes)
3. `recalcular_orcamento_mes` para categorias/periodos afetados (antes e depois)
4. `db.commit()` + `db.refresh()`

---

## Regras de Exclusão (`TransacaoService.deletar`)

- `e_dizimo=True` → não pode deletar diretamente (`ValueError`)
- Se `tem_dizimo=True`: busca e apaga o dízimo relacionado, reverte saldo do dízimo
- `conta.saldo -= impacto_no_saldo(transacao)`
- Recalcula metas e orçamentos afetados
- `db.commit()`

---

## Regras de Duplicação (`TransacaoService.duplicar`)

- `e_dizimo=True` → não pode duplicar diretamente (`ValueError`)
- **Parcelado**: cria cópia única com data=hoje, `status=PREVISTO`, novo `grupo_parcelamento_uuid`
  - Não cria as demais parcelas — é uma cópia avulsa
  - **Não** atualiza `conta.saldo` (status=PREVISTO → impacto=0)
- **Não parcelado**: delega para `criar(TransacaoCreate(...))`
  - Preserva `tem_dizimo` se era entrada com dízimo

---

## Metas (`domain/transacao.recalcular_meta`)

```python
meta.valor_atual = sum(valor_meta(t) for t in transacoes onde meta_id == meta.id)
meta.concluida = meta.valor_atual >= meta.valor_alvo
```

- Triggered: sempre que `meta_id` está envolvido em criar/atualizar/deletar
- Não tem índice de busca por meta_id — full scan filtrado por user_id

---

## Orçamentos (`domain/transacao.recalcular_orcamento_mes`)

```python
orcamento.valor_gasto = sum(
    valor_efetivo(t) for t in transacoes
    where categoria_id == orcamento.categoria_id
    and mes/ano == orcamento.mes/ano
    and tipo == SAIDA
    and status != CANCELADO
)
```

- Triggered: apenas para SAÍDAS com `categoria_id` não nulo
- Afetados: categoria antes + categoria depois (no update)
- Orçamento inexistente → nenhuma ação (não cria)

---

## Cartão / Fatura (`domain/cartao_fatura`)

### Competência vs. Mês da Compra
A compra pertence à **competência** do fechamento que a engloba.
`data_compra` cai no período `(fechamento_anterior + 1 dia, fechamento_atual)`.

### Cálculo de período
```
periodo_fim   = data_fechamento_prevista (ou real, se override)
periodo_inicio = data_fechamento_anterior + 1 dia
```

### Cálculo de vencimento
```
if dia_vencimento > dia_do_fechamento:
    vencimento = dia_vencimento no mesmo mês do fechamento
else:
    vencimento = dia_vencimento no mês seguinte ao fechamento
```

### Override por ciclo (`ContaCartaoCiclo`)
Tabela que permite sobrescrever `data_fechamento_real` e `data_vencimento_real`
para uma competência específica (fechamento antecipado, feriados).

### ResumoFatura
```
valor_total   = sum(saidas) - sum(entradas)
valor_pago    = sum(saidas LIQUIDADO)
valor_a_pagar = sum(saidas PREVISTO|ATRASADO) - sum(entradas)
```

---

## Dependências Cruzadas

```
criar_transacao
  ├─ Conta (saldo)
  ├─ Meta (recalcular_meta) — se meta_id
  ├─ Orcamento (recalcular_orcamento_mes) — se saida + categoria
  └─ Categoria (obter_categoria_dizimo) — se tem_dizimo

atualizar_transacao
  ├─ Conta origem + Conta destino (saldo)
  ├─ Transacao dizimo (atualizar ou criar ou apagar)
  ├─ Meta antiga + Meta nova (recalcular)
  └─ Orcamento categoria/periodo antes + depois

deletar_transacao
  ├─ Conta (saldo)
  ├─ Transacao dizimo (apagar em cascata)
  ├─ Meta (recalcular)
  └─ Orcamento (recalcular)
```
