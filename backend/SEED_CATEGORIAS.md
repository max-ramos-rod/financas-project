# 🌱 Seed de Categorias Padrão

## O que são Categorias Padrão?

Categorias padrão são categorias **criadas pelo sistema** e disponíveis para **todos os usuários**.

Características:
- `user_id = NULL` → Não pertencem a ninguém
- `padrao = True` → Marcadas como padrão
- Aparecem para todos os usuários
- Usuários **NÃO podem deletar** (só suas próprias categorias)

---

## 📊 Categorias Incluídas

### Total: 44 categorias

**📈 Entradas (6):**
- 💰 Salário
- 💼 Freelance
- 📈 Investimentos
- 🎁 Presente Recebido
- 🏷️ Venda
- ➕ Outras Receitas

**📉 Saídas (37):**

**Moradia (6):**
- 🏠 Aluguel
- 🏢 Condomínio
- ⚡ Energia
- 💧 Água
- 🌐 Internet
- 🔥 Gás

**Alimentação (3):**
- 🛒 Mercado
- 🍽️ Restaurante
- 🍔 Lanche

**Transporte (4):**
- ⛽ Combustível
- 🚌 Transporte Público
- 🚕 Uber/Taxi
- 🅿️ Estacionamento

**Saúde (3):**
- 💊 Farmácia
- ⚕️ Médico
- 🏥 Plano de Saúde

**Educação (3):**
- 🎓 Mensalidade Escola
- 📚 Livros
- 💻 Cursos

**Lazer (4):**
- 🎬 Cinema
- 📺 Streaming
- ✈️ Viagem
- 🏋️ Academia

**Pessoal (3):**
- 👕 Vestuário
- 💇 Cabeleireiro
- 💄 Cosméticos

**Outros (5):**
- 💳 Cartão de Crédito
- 🏦 Empréstimo
- 🎁 Presente Dado
- 🐕 Pet
- 📌 Outros

**Cristãs (6):**
- ⛪ Dízimo
- 🙏 Oferta
- 🌍 Missões
- ⛺ Acampamento/Retiro
- 📖 Literatura Cristã
- 🎓 Seminário

**🔄 Flexíveis (1):**
- 🔄 Transferência (pode ser entrada ou saída)

---

## 🚀 Como Usar

### 1. Primeira Instalação

Após rodar as migrations:

```bash
cd backend
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

### 2. Listar Categorias Criadas

```bash
python seed_categorias.py --listar
```

**Saída:**
```
📋 CATEGORIAS PADRÃO DO SISTEMA:

==================================================
📈 ENTRADAS
==================================================

💰  Salário                        (cor: #10B981)
💼  Freelance                      (cor: #3B82F6)
📈  Investimentos                  (cor: #8B5CF6)
...
```

### 3. Recriar Categorias

Se precisar atualizar as categorias padrão:

```bash
python seed_categorias.py
```

Sistema perguntará:
```
⚠️  Já existem 44 categorias padrão no banco.
Deseja recriar? (s/N):
```

Digite `s` para confirmar.

---

## 🔧 Quando Rodar o Seed?

### ✅ Rode o seed:

1. **Primeira instalação** do sistema
2. **Após adicionar novas categorias** no código
3. **Em ambientes de desenvolvimento** (sempre que recriar o banco)
4. **Quando adicionar novos servidores** (produção, staging)

### ❌ NÃO rode o seed:

1. **Se usuários já criaram categorias customizadas** (não afeta, mas é desnecessário)
2. **Toda vez que rodar a aplicação** (só uma vez é suficiente)

---

## 📝 Adicionando Novas Categorias Padrão

### Editando o arquivo

Abra `seed_categorias.py` e adicione na lista `CATEGORIAS_PADRAO`:

```python
CATEGORIAS_PADRAO = [
    # ... categorias existentes ...
    
    # Nova categoria
    {
        "nome": "Delivery",
        "icone": "🛵",
        "cor": "#F59E0B",
        "tipo": "saida",
        "descricao": "Pedidos de delivery"
    },
]
```

Depois rode:
```bash
python seed_categorias.py
```

---

## 🎨 Escolhendo Cores

Use cores hexadecimais do TailwindCSS para consistência:

```python
# Verde (sucesso, positivo)
"#10B981"  # green-500
"#059669"  # green-600

# Vermelho (despesas, negativo)
"#EF4444"  # red-500
"#DC2626"  # red-600

# Azul (neutro, informação)
"#3B82F6"  # blue-500
"#2563EB"  # blue-600

# Roxo (premium, especial)
"#8B5CF6"  # purple-500
"#7C3AED"  # purple-600

# Amarelo (atenção, variável)
"#F59E0B"  # amber-500
"#F97316"  # orange-500

# Cinza (outros, diversos)
"#6B7280"  # gray-500
```

---

## 🔍 Como Funciona no Sistema

### 1. Backend - Consulta de Categorias

```python
# api/v1/endpoints/categorias.py

@router.get("/")
def listar_categorias(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista categorias padrão + categorias do usuário"""
    categorias = db.query(Categoria).filter(
        # Categorias do sistema OU categorias do usuário
        (Categoria.user_id == None) | (Categoria.user_id == current_user.id)
    ).all()
    
    return categorias
```

**Resultado para usuário ID=5:**
```json
[
  {"id": 1, "user_id": null, "nome": "Salário", "padrao": true},
  {"id": 2, "user_id": null, "nome": "Mercado", "padrao": true},
  ...
  {"id": 50, "user_id": 5, "nome": "Ração do Dog", "padrao": false}
]
```

### 2. Frontend - Exibição

```vue
<template>
  <select v-model="categoria_id">
    <optgroup label="Categorias Padrão">
      <option v-for="cat in categoriasPadrao" :value="cat.id">
        {{ cat.icone }} {{ cat.nome }}
      </option>
    </optgroup>
    
    <optgroup label="Minhas Categorias" v-if="minhasCategorias.length > 0">
      <option v-for="cat in minhasCategorias" :value="cat.id">
        {{ cat.icone }} {{ cat.nome }}
      </option>
    </optgroup>
  </select>
</template>

<script setup lang="ts">
const categoriasPadrao = computed(() => 
  categorias.value.filter(c => c.padrao)
)

const minhasCategorias = computed(() => 
  categorias.value.filter(c => !c.padrao)
)
</script>
```

---

## ⚙️ Integração com Alembic (Alternativa)

Se preferir rodar o seed **automaticamente** nas migrations:

**`backend/alembic/versions/xxxx_seed_categorias.py`:**

```python
"""seed categorias padrão

Revision ID: xxxx
Revises: yyyy
Create Date: 2024-02-06
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Importa o script de seed
    import sys
    sys.path.append('.')
    from seed_categorias import CATEGORIAS_PADRAO
    
    # Insere categorias
    categorias_table = sa.table('categorias',
        sa.column('user_id', sa.Integer),
        sa.column('nome', sa.String),
        sa.column('icone', sa.String),
        sa.column('cor', sa.String),
        sa.column('tipo', sa.String),
        sa.column('padrao', sa.Boolean),
    )
    
    op.bulk_insert(categorias_table, CATEGORIAS_PADRAO)

def downgrade() -> None:
    op.execute("DELETE FROM categorias WHERE padrao = true")
```

**Vantagens:**
- Roda automaticamente com `alembic upgrade head`
- Versionado com as migrations

**Desvantagens:**
- Mais difícil de atualizar categorias depois
- Menos flexível

**Recomendação:** Use o **script separado** (`seed_categorias.py`) para mais flexibilidade.

---

## 🐛 Troubleshooting

### Erro: "No module named 'app'"

```bash
# Rode a partir da pasta backend
cd backend
python seed_categorias.py
```

### Erro: "categorias.tipo violates check constraint"

O campo `tipo` aceita apenas: `"entrada"`, `"saida"`, ou `None`.

Verifique se usou o valor correto:
```python
"tipo": "entrada"  # ✅ Correto
"tipo": "ENTRADA"  # ❌ Errado (case sensitive)
"tipo": None       # ✅ Correto (flexível)
```

### Categorias duplicadas

Se rodou o seed múltiplas vezes sem confirmar a recriação:

```bash
# Limpar manualmente
python
>>> from app.db.session import SessionLocal
>>> from app.models import Categoria
>>> db = SessionLocal()
>>> db.query(Categoria).filter(Categoria.padrao == True).delete()
>>> db.commit()
>>> exit()

# Rodar seed novamente
python seed_categorias.py
```

---

## 📋 Checklist de Instalação

- [ ] Criar banco de dados PostgreSQL
- [ ] Configurar `.env` com `DATABASE_URL`
- [ ] Rodar migrations: `alembic upgrade head`
- [ ] **Rodar seed: `python seed_categorias.py`** ← AQUI
- [ ] Iniciar backend: `uvicorn app.main:app --reload`
- [ ] Verificar: `/api/v1/categorias` deve retornar 44 categorias

---

## 🎯 Resumo

| O que | Onde | Quando |
|-------|------|--------|
| Categorias padrão | `seed_categorias.py` | Após migrations |
| 44 categorias | 6 entradas + 37 saídas + 1 flexível | Uma vez |
| Listar | `python seed_categorias.py --listar` | Para verificar |
| Recriar | `python seed_categorias.py` → s | Ao atualizar |

**Pronto!** Todos os usuários terão 44 categorias disponíveis imediatamente. 🎉
