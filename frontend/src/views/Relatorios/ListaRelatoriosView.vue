<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import type { Transacao, Conta, Categoria } from '@/types'

const router = useRouter()

// State
const loading = ref(true)
const transacoes = ref<Transacao[]>([])
const contas = ref<Conta[]>([])
const categorias = ref<Categoria[]>([])

// Filtros
const filtros = ref({
  tipo: 'todas' as 'todas' | 'entrada' | 'saida',
  conta_id: null as number | null,
  categoria_id: null as number | null,
  mes: new Date().getMonth() + 1,
  ano: new Date().getFullYear(),
  busca: ''
})

// Computed - Transações Filtradas
const transacoesFiltradas = computed(() => {
  let resultado = [...transacoes.value]
  
  // Filtro por tipo
  if (filtros.value.tipo !== 'todas') {
    resultado = resultado.filter(t => t.tipo === filtros.value.tipo)
  }
  
  // Filtro por conta
  if (filtros.value.conta_id) {
    resultado = resultado.filter(t => t.conta_id === filtros.value.conta_id)
  }
  
  // Filtro por categoria
  if (filtros.value.categoria_id) {
    resultado = resultado.filter(t => t.categoria_id === filtros.value.categoria_id)
  }
  
  // Filtro por mês/ano
  resultado = resultado.filter(t => {
    const data = new Date(t.data)
    return (
      data.getMonth() + 1 === filtros.value.mes &&
      data.getFullYear() === filtros.value.ano
    )
  })
  
  // Busca textual
  if (filtros.value.busca) {
    const busca = filtros.value.busca.toLowerCase()
    resultado = resultado.filter(t =>
      t.descricao.toLowerCase().includes(busca)
    )
  }
  
  // Ordena por data (mais recente primeiro)
  resultado.sort((a, b) => new Date(b.data).getTime() - new Date(a.data).getTime())
  
  return resultado
})

// Computed - Totais
const totais = computed(() => {
  const entradas = transacoesFiltradas.value
    .filter(t => t.tipo === 'entrada')
    .reduce((sum, t) => sum + t.valor, 0)
  
  const saidas = transacoesFiltradas.value
    .filter(t => t.tipo === 'saida')
    .reduce((sum, t) => sum + t.valor, 0)
  
  return {
    entradas,
    saidas,
    saldo: entradas - saidas
  }
})

// Computed - Agrupar por Data
const transacoesAgrupadasPorData = computed(() => {
  const grupos: Record<string, Transacao[]> = {}
  
  transacoesFiltradas.value.forEach(t => {
    const dataKey = formatarData(t.data)
    if (!grupos[dataKey]) {
      grupos[dataKey] = []
    }
    grupos[dataKey].push(t)
  })
  
  return Object.entries(grupos).map(([data, transacoes]) => ({
    data,
    transacoes
  }))
})

// Métodos
const fetchDados = async () => {
  loading.value = true
  try {
    const [transacoesRes, contasRes, categoriasRes] = await Promise.all([
      api.get('/transacoes'),
      api.get('/contas'),
      api.get('/categorias')
    ])
    
    transacoes.value = transacoesRes.data
    contas.value = contasRes.data
    categorias.value = categoriasRes.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loading.value = false
  }
}

const novaTransacao = () => {
  router.push('/transacoes/nova')
}

const editarTransacao = (id: number) => {
  router.push(`/transacoes/${id}/editar`)
}

const deletarTransacao = async (id: number) => {
  if (!confirm('Tem certeza que deseja excluir esta transação?')) return
  
  try {
    await api.delete(`/transacoes/${id}`)
    transacoes.value = transacoes.value.filter(t => t.id !== id)
  } catch (error) {
    console.error('Erro ao deletar:', error)
    alert('Erro ao excluir transação')
  }
}

const formatarMoeda = (valor: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)
}

const formatarData = (data: string): string => {
  return new Date(data).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const getCategoriaInfo = (categoriaId: number | null) => {
  if (!categoriaId) return { nome: 'Sem Categoria', icone: '📌', cor: '#6B7280' }
  const categoria = categorias.value.find(c => c.id === categoriaId)
  return {
    nome: categoria?.nome || 'Sem Categoria',
    icone: categoria?.icone || '📌',
    cor: categoria?.cor || '#6B7280'
  }
}

const limparFiltros = () => {
  filtros.value = {
    tipo: 'todas',
    conta_id: null,
    categoria_id: null,
    mes: new Date().getMonth() + 1,
    ano: new Date().getFullYear(),
    busca: ''
  }
}

onMounted(() => {
  fetchDados()
})
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="container mx-auto px-4 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-2xl font-bold">Transações</h1>
          <button @click="novaTransacao" class="btn btn-primary">
            ➕ Nova Transação
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">Carregando transações...</p>
    </div>

    <!-- Content -->
    <div v-else class="container mx-auto px-4 py-8">
      
      <!-- Filtros -->
      <div class="card bg-white shadow-md mb-6">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title">Filtros</h3>
            <button @click="limparFiltros" class="btn btn-ghost btn-sm">
              Limpar Filtros
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <!-- Busca -->
            <div class="lg:col-span-2">
              <input
                v-model="filtros.busca"
                type="text"
                placeholder="🔍 Buscar por descrição..."
                class="input input-bordered w-full"
              />
            </div>

            <!-- Tipo -->
            <div>
              <select v-model="filtros.tipo" class="select select-bordered w-full">
                <option value="todas">Todas</option>
                <option value="entrada">📈 Entradas</option>
                <option value="saida">📉 Saídas</option>
              </select>
            </div>

            <!-- Mês/Ano -->
            <div class="flex gap-2">
              <select v-model.number="filtros.mes" class="select select-bordered flex-1">
                <option :value="1">Jan</option>
                <option :value="2">Fev</option>
                <option :value="3">Mar</option>
                <option :value="4">Abr</option>
                <option :value="5">Mai</option>
                <option :value="6">Jun</option>
                <option :value="7">Jul</option>
                <option :value="8">Ago</option>
                <option :value="9">Set</option>
                <option :value="10">Out</option>
                <option :value="11">Nov</option>
                <option :value="12">Dez</option>
              </select>
              <input
                v-model.number="filtros.ano"
                type="number"
                class="input input-bordered w-24"
              />
            </div>

            <!-- Conta -->
            <div>
              <select v-model="filtros.conta_id" class="select select-bordered w-full">
                <option :value="null">Todas as contas</option>
                <option v-for="conta in contas" :key="conta.id" :value="conta.id">
                  {{ conta.nome }}
                </option>
              </select>
            </div>

            <!-- Categoria -->
            <div>
              <select v-model="filtros.categoria_id" class="select select-bordered w-full">
                <option :value="null">Todas categorias</option>
                <option v-for="cat in categorias" :key="cat.id" :value="cat.id">
                  {{ cat.icone }} {{ cat.nome }}
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumo -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Total Entradas</p>
            <p class="text-2xl font-bold text-success">{{ formatarMoeda(totais.entradas) }}</p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Total Saídas</p>
            <p class="text-2xl font-bold text-error">{{ formatarMoeda(totais.saidas) }}</p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Saldo do Período</p>
            <p :class="['text-2xl font-bold', totais.saldo >= 0 ? 'text-success' : 'text-error']">
              {{ formatarMoeda(totais.saldo) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Lista de Transações -->
      <div v-if="transacoesFiltradas.length === 0" class="card bg-white shadow-md">
        <div class="card-body text-center py-16">
          <div class="text-6xl mb-4">📭</div>
          <p class="text-xl font-semibold mb-2">Nenhuma transação encontrada</p>
          <p class="text-gray-500 mb-6">
            {{ filtros.tipo !== 'todas' || filtros.conta_id || filtros.categoria_id || filtros.busca
              ? 'Tente ajustar os filtros'
              : 'Adicione sua primeira transação' }}
          </p>
          <button @click="novaTransacao" class="btn btn-primary">
            ➕ Nova Transação
          </button>
        </div>
      </div>

      <!-- Transações Agrupadas por Data -->
      <div v-else class="space-y-6">
        <div v-for="grupo in transacoesAgrupadasPorData" :key="grupo.data">
          <!-- Cabeçalho da Data -->
          <div class="flex items-center gap-4 mb-3">
            <h3 class="text-lg font-semibold">{{ grupo.data }}</h3>
            <div class="flex-1 h-px bg-gray-300"></div>
          </div>

          <!-- Cards de Transação -->
          <div class="space-y-3">
            <div
              v-for="transacao in grupo.transacoes"
              :key="transacao.id"
              class="card bg-white shadow-sm hover:shadow-md transition-shadow"
            >
              <div class="card-body p-4">
                <div class="flex items-start gap-4">
                  <!-- Ícone da Categoria -->
                  <div class="text-3xl">
                    {{ getCategoriaInfo(transacao.categoria_id).icone }}
                  </div>

                  <!-- Informações -->
                  <div class="flex-1 min-w-0">
                    <div class="flex justify-between items-start gap-4">
                      <div class="flex-1">
                        <h4 class="font-semibold truncate">{{ transacao.descricao }}</h4>
                        <div class="flex flex-wrap items-center gap-2 mt-1">
                          <span class="text-xs badge badge-ghost">
                            {{ getCategoriaInfo(transacao.categoria_id).nome }}
                          </span>
                          
                          <span v-if="transacao.fixa" class="text-xs badge badge-info">
                            📌 Fixa
                          </span>
                          
                          <span v-if="transacao.recorrente" class="text-xs badge badge-warning">
                            🔄 Recorrente
                          </span>
                          
                          <span v-if="transacao.parcelado" class="text-xs badge badge-secondary">
                            💳 {{ transacao.parcela_atual }}/{{ transacao.total_parcelas }}
                          </span>
                          
                          <span v-if="transacao.e_dizimo" class="text-xs badge badge-success">
                            ⛪ Dízimo
                          </span>
                          
                          <span v-if="transacao.e_emprestimo" class="text-xs badge badge-error">
                            🏦 {{ transacao.pessoa_emprestimo }}
                          </span>
                        </div>
                      </div>

                      <!-- Valor -->
                      <div class="text-right">
                        <p :class="[
                          'text-xl font-bold',
                          transacao.tipo === 'entrada' ? 'text-success' : 'text-error'
                        ]">
                          {{ transacao.tipo === 'entrada' ? '+' : '-' }} {{ formatarMoeda(transacao.valor) }}
                        </p>
                      </div>
                    </div>

                    <!-- Observações -->
                    <p v-if="transacao.observacoes" class="text-sm text-gray-500 mt-2">
                      {{ transacao.observacoes }}
                    </p>
                  </div>

                  <!-- Ações -->
                  <div class="dropdown dropdown-end">
                    <label tabindex="0" class="btn btn-ghost btn-sm btn-circle">
                      ⋮
                    </label>
                    <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                      <li>
                        <a @click="editarTransacao(transacao.id)">
                          ✏️ Editar
                        </a>
                      </li>
                      <li>
                        <a @click="deletarTransacao(transacao.id)" class="text-error">
                          🗑️ Excluir
                        </a>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contador -->
      <div class="text-center mt-8 text-gray-500">
        {{ transacoesFiltradas.length }} transação(ões) encontrada(s)
      </div>
    </div>
  </div>
</template>
