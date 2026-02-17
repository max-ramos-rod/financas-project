<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import type { Orcamento, Categoria } from '@/types'

const router = useRouter()

// State
const loading = ref(true)
const orcamentos = ref<Orcamento[]>([])
const categorias = ref<Categoria[]>([])
const orcamentoADeletar = ref<Orcamento | null>(null)
const mostraModalDelete = ref(false)
const showErrorModal = ref(false)
const errorMessages = ref<string[]>([])

function formatApiError(error: any): string[] {
  const detail = error?.response?.data?.detail
  if (!detail) return [error?.message || 'Erro desconhecido']
  if (Array.isArray(detail)) {
    return detail.map(d => {
      if (typeof d === 'string') return d
      if (d?.msg && d?.loc) return `${d.loc.join('.')} — ${d.msg}`
      return JSON.stringify(d)
    })
  }
  if (typeof detail === 'object') {
    if (detail.msg) return [detail.msg]
    return [JSON.stringify(detail)]
  }
  return [String(detail)]
}

// Filtros
const mesAtual = new Date().getMonth() + 1
const anoAtual = new Date().getFullYear()

const filtros = ref({
  mes: mesAtual,
  ano: anoAtual
})

// Computed - Orçamentos Filtrados
const orcamentosFiltrados = computed(() => {
  return orcamentos.value.filter(o =>
    o.mes === filtros.value.mes && o.ano === filtros.value.ano
  )
})

// Computed - Totais
const totais = computed(() => {
  const planejado = orcamentosFiltrados.value.reduce((sum, o) => sum + o.valor_planejado, 0)
  const gasto = orcamentosFiltrados.value.reduce((sum, o) => sum + o.valor_gasto, 0)
  const restante = planejado - gasto
  
  return {
    planejado,
    gasto,
    restante,
    percentualGasto: planejado > 0 ? (gasto / planejado) * 100 : 0
  }
})

// Métodos
const fetchDados = async () => {
  loading.value = true
  try {
    const [orcamentosRes, categoriasRes] = await Promise.all([
      api.get('/orcamentos', {
        params: {
          mes: filtros.value.mes,
          ano: filtros.value.ano
        }
      }),
      api.get('/categorias')
    ])
    
    orcamentos.value = orcamentosRes.data
    categorias.value = categoriasRes.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loading.value = false
  }
}

const novoOrcamento = () => {
  router.push('/orcamentos/novo')
}

const editarOrcamento = (id: number) => {
  router.push(`/orcamentos/${id}/editar`)
}

const abrirModalDelete = (orcamento: Orcamento) => {
  orcamentoADeletar.value = orcamento
  mostraModalDelete.value = true
}

const fecharModalDelete = () => {
  mostraModalDelete.value = false
  orcamentoADeletar.value = null
}

const deletarOrcamento = async () => {
  if (!orcamentoADeletar.value) return
  
  const id = orcamentoADeletar.value.id
  
  try {
    await api.delete(`/orcamentos/${id}`)
    orcamentos.value = orcamentos.value.filter(o => o.id !== id)
    fecharModalDelete()
  } catch (error) {
    console.error('Erro ao deletar:', error)
    errorMessages.value = formatApiError(error)
    showErrorModal.value = true
  }
}

const formatarMoeda = (valor: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)
}

const getCategoriaInfo = (categoriaId: number) => {
  const categoria = categorias.value.find(c => c.id === categoriaId)
  return {
    nome: categoria?.nome || 'Sem Categoria',
    icone: categoria?.icone || '📌',
    cor: categoria?.cor || '#6B7280'
  }
}

const getMeses = () => [
  { valor: 1, label: 'Janeiro' },
  { valor: 2, label: 'Fevereiro' },
  { valor: 3, label: 'Março' },
  { valor: 4, label: 'Abril' },
  { valor: 5, label: 'Maio' },
  { valor: 6, label: 'Junho' },
  { valor: 7, label: 'Julho' },
  { valor: 8, label: 'Agosto' },
  { valor: 9, label: 'Setembro' },
  { valor: 10, label: 'Outubro' },
  { valor: 11, label: 'Novembro' },
  { valor: 12, label: 'Dezembro' }
]

const atualizarFiltros = () => {
  fetchDados()
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
          <h1 class="text-2xl font-bold">💼 Orçamentos</h1>
          <button @click="novoOrcamento" class="btn btn-primary">
            ➕ Novo Orçamento
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">Carregando orçamentos...</p>
    </div>

    <!-- Content -->
    <div v-else class="container mx-auto px-4 py-8">
      
      <!-- Filtros -->
      <div class="card bg-white shadow-md mb-6">
        <div class="card-body">
          <h3 class="card-title mb-4">📅 Período</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Mês -->
            <div>
              <label class="label">
                <span class="label-text">Mês</span>
              </label>
              <select v-model.number="filtros.mes" @change="atualizarFiltros" class="select select-bordered w-full">
                <option v-for="mes in getMeses()" :key="mes.valor" :value="mes.valor">
                  {{ mes.label }}
                </option>
              </select>
            </div>

            <!-- Ano -->
            <div>
              <label class="label">
                <span class="label-text">Ano</span>
              </label>
              <input
                v-model.number="filtros.ano"
                @change="atualizarFiltros"
                type="number"
                class="input input-bordered w-full"
              />
            </div>

            <!-- Info -->
            <div class="flex items-end">
              <p class="text-sm text-gray-500">
                Mostrando {{ orcamentosFiltrados.length }} orçamento(s)
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumo -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Planejado</p>
            <p class="text-2xl font-bold text-info">{{ formatarMoeda(totais.planejado) }}</p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Gasto</p>
            <p class="text-2xl font-bold text-error">{{ formatarMoeda(totais.gasto) }}</p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Restante</p>
            <p :class="['text-2xl font-bold', totais.restante >= 0 ? 'text-success' : 'text-error']">
              {{ formatarMoeda(totais.restante) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Utilizado</p>
            <p class="text-2xl font-bold">{{ totais.percentualGasto.toFixed(1) }}%</p>
          </div>
        </div>
      </div>

      <!-- Lista de Orçamentos -->
      <div v-if="orcamentosFiltrados.length === 0" class="card bg-white shadow-md">
        <div class="card-body text-center py-16">
          <div class="text-6xl mb-4">💼</div>
          <p class="text-xl font-semibold mb-2">Nenhum orçamento encontrado</p>
          <p class="text-gray-500 mb-6">
            Crie seu primeiro orçamento para acompanhar seus gastos
          </p>
          <button @click="novoOrcamento" class="btn btn-primary">
            ➕ Novo Orçamento
          </button>
        </div>
      </div>

      <!-- Cards de Orçamentos -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="orcamento in orcamentosFiltrados"
          :key="orcamento.id"
          class="card bg-white shadow-md hover:shadow-lg transition-shadow"
        >
          <div class="card-body">
            <!-- Header -->
            <div class="flex items-start gap-3 mb-4">
              <div class="text-3xl">{{ getCategoriaInfo(orcamento.categoria_id).icone }}</div>
              <div class="flex-1">
                <h3 class="card-title text-lg">{{ getCategoriaInfo(orcamento.categoria_id).nome }}</h3>
                <p class="text-sm text-gray-500">Orçamento</p>
              </div>
            </div>

            <!-- Valores -->
            <div class="space-y-2 mb-4">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Planejado:</span>
                <span class="font-bold">{{ formatarMoeda(orcamento.valor_planejado) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Gasto:</span>
                <span :class="['font-bold', orcamento.valor_gasto > orcamento.valor_planejado ? 'text-error' : 'text-success']">
                  {{ formatarMoeda(orcamento.valor_gasto) }}
                </span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Restante:</span>
                <span :class="['font-bold', orcamento.valor_planejado - orcamento.valor_gasto >= 0 ? 'text-success' : 'text-error']">
                  {{ formatarMoeda(orcamento.valor_planejado - orcamento.valor_gasto) }}
                </span>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="mb-4">
              <div class="flex justify-between items-center mb-2">
                <span class="text-xs font-semibold">Progresso</span>
                <span class="text-xs font-bold">
                  {{ ((orcamento.valor_gasto / orcamento.valor_planejado) * 100).toFixed(1) }}%
                </span>
              </div>
              <progress
                class="progress h-3 w-full"
                :value="orcamento.valor_gasto"
                :max="orcamento.valor_planejado"
                :style="{ 
                  accentColor: orcamento.valor_gasto > orcamento.valor_planejado ? '#ef4444' : '#10b981'
                }"
              ></progress>
            </div>

            <!-- Alert se exceder -->
            <div v-if="orcamento.valor_gasto > orcamento.valor_planejado" class="alert alert-error alert-sm mb-4">
              <div class="text-xs">
                ⚠️ Orçamento excedido em {{ formatarMoeda(orcamento.valor_gasto - orcamento.valor_planejado) }}
              </div>
            </div>

            <!-- Ações -->
            <div class="card-actions justify-end pt-4 border-t">
              <button
                @click="editarOrcamento(orcamento.id)"
                class="btn btn-sm btn-ghost"
              >
                ✏️ Editar
              </button>
              <button
                @click="abrirModalDelete(orcamento)"
                class="btn btn-sm btn-ghost text-error"
              >
                🗑️ Deletar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de Confirmação de Deleção -->
    <div v-if="mostraModalDelete" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">🗑️ Excluir Orçamento</h3>
        <p class="py-4 text-gray-600">
          Tem certeza que deseja excluir o orçamento de <strong>"{{ getCategoriaInfo(orcamentoADeletar?.categoria_id || 0).nome }}"</strong>?
        </p>
        <p class="text-sm text-gray-500 mb-4">
          Valor planejado: <strong>{{ formatarMoeda(orcamentoADeletar?.valor_planejado || 0) }}</strong>
        </p>
        <p class="text-sm text-error font-semibold">
          ⚠️ Esta ação não pode ser desfeita!
        </p>

        <div class="modal-action gap-2 mt-6">
          <button @click="fecharModalDelete" class="btn btn-ghost">
            Cancelar
          </button>
          <button @click="deletarOrcamento" class="btn btn-error">
            Excluir Orçamento
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="fecharModalDelete">close</button>
      </form>
    </div>
    <!-- Modal de Erro -->
    <div v-if="showErrorModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">❗ Erro</h3>
        <div class="space-y-2 text-sm text-gray-700">
          <p v-for="(m, i) in errorMessages" :key="i">• {{ m }}</p>
        </div>
        <div class="modal-action mt-6">
          <button @click="showErrorModal = false" class="btn btn-ghost">Fechar</button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="showErrorModal = false">close</button>
      </form>
    </div>    
  </div>
</template>