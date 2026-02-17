<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import type { Meta } from '@/types'

const router = useRouter()

// State
const loading = ref(true)
const metas = ref<Meta[]>([])
const metaADeletar = ref<Meta | null>(null)
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
const filtros = ref({
  status: 'todas' as 'todas' | 'ativas' | 'concluidas',
  busca: ''
})

// Computed - Metas Filtradas
const metasFiltradas = computed(() => {
  let resultado = [...metas.value]
  
  // Filtro por status
  if (filtros.value.status === 'ativas') {
    resultado = resultado.filter(m => !m.concluida)
  } else if (filtros.value.status === 'concluidas') {
    resultado = resultado.filter(m => m.concluida)
  }
  
  // Busca textual
  if (filtros.value.busca) {
    const busca = filtros.value.busca.toLowerCase()
    resultado = resultado.filter(m =>
      m.nome.toLowerCase().includes(busca) ||
      (m.descricao && m.descricao.toLowerCase().includes(busca))
    )
  }
  
  // Ordena por data de criação (mais recentes primeiro)
  resultado.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  
  return resultado
})

// Computed - Totais
const totais = computed(() => {
  const ativas = metas.value.filter(m => !m.concluida).length
  const concluidas = metas.value.filter(m => m.concluida).length
  
  return {
    ativas,
    concluidas,
    total: metas.value.length
  }
})

// Métodos
const fetchDados = async () => {
  loading.value = true
  try {
    const metasRes = await api.get('/metas')
    metas.value = metasRes.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loading.value = false
  }
}

const novaMeta = () => {
  router.push('/metas/nova')
}

const editarMeta = (id: number) => {
  router.push(`/metas/${id}/editar`)
}

const abrirModalDelete = (meta: Meta) => {
  console.log("TESTANDO A PACIENCIA NA VIDA.")
  metaADeletar.value = meta
  mostraModalDelete.value = true
}

const fecharModalDelete = () => {
  mostraModalDelete.value = false
  metaADeletar.value = null
}

const deletarMeta = async () => {
  if (!metaADeletar.value) return
  
  const id = metaADeletar.value.id
  
  try {
    await api.delete(`/metas/${id}`)
    metas.value = metas.value.filter(m => m.id !== id)
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

const formatarData = (data: string): string => {
  return new Date(data).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  })
}

const calcularProgresso = (meta: Meta): number => {
  return Math.min(100, (meta.valor_atual / meta.valor_alvo) * 100)
}

const limparFiltros = () => {
  filtros.value = {
    status: 'todas',
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
          <h1 class="text-2xl font-bold">🎯 Metas</h1>
          <button @click="novaMeta" class="btn btn-primary">
            ➕ Nova Meta
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">Carregando metas...</p>
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

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Busca -->
            <div>
              <input
                v-model="filtros.busca"
                type="text"
                placeholder="🔍 Buscar por nome ou descrição..."
                class="input input-bordered w-full"
              />
            </div>

            <!-- Status -->
            <div>
              <select v-model="filtros.status" class="select select-bordered w-full">
                <option value="todas">Todas as Metas</option>
                <option value="ativas">✏️ Ativas</option>
                <option value="concluidas">✅ Concluídas</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumo -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Total de Metas</p>
            <p class="text-2xl font-bold">{{ totais.total }}</p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Metas Ativas</p>
            <p class="text-2xl font-bold text-warning">{{ totais.ativas }}</p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Metas Concluídas</p>
            <p class="text-2xl font-bold text-success">{{ totais.concluidas }}</p>
          </div>
        </div>
      </div>

      <!-- Lista de Metas -->
      <div v-if="metasFiltradas.length === 0" class="card bg-white shadow-md">
        <div class="card-body text-center py-16">
          <div class="text-6xl mb-4">🎯</div>
          <p class="text-xl font-semibold mb-2">Nenhuma meta encontrada</p>
          <p class="text-gray-500 mb-6">
            {{ filtros.status !== 'todas' || filtros.busca
              ? 'Tente ajustar os filtros'
              : 'Adicione sua primeira meta de economias' }}
          </p>
          <button @click="novaMeta" class="btn btn-primary">
            ➕ Nova Meta
          </button>
        </div>
      </div>

      <!-- Cards de Metas -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="meta in metasFiltradas"
          :key="meta.id"
          class="card bg-white shadow-md hover:shadow-lg transition-shadow"
          :style="{ borderTop: `4px solid ${meta.cor}` }"
        >
          <div class="card-body">
            <!-- Header -->
            <div class="flex justify-between items-start mb-3">
              <div class="flex-1">
                <h3 class="card-title text-lg">{{ meta.nome }}</h3>
                <p v-if="meta.descricao" class="text-sm text-gray-500 mt-1">
                  {{ meta.descricao }}
                </p>
              </div>

              <!-- Status Badge -->
              <div v-if="meta.concluida" class="badge badge-success">
                ✅ Concluída
              </div>
              <div v-else class="badge badge-warning">
                ✏️ Ativa
              </div>
            </div>

            <!-- Datas -->
            <div class="flex justify-between text-sm text-gray-500 mb-4">
              <span>📅 {{ formatarData(meta.data_inicio) }}</span>
              <span v-if="meta.data_fim">até {{ formatarData(meta.data_fim) }}</span>
            </div>

            <!-- Valores -->
            <div class="mb-4">
              <div class="flex justify-between items-center mb-2">
                <p class="text-sm font-semibold">Progresso</p>
                <p class="text-sm font-bold">
                  {{ formatarMoeda(meta.valor_atual) }} / {{ formatarMoeda(meta.valor_alvo) }}
                </p>
              </div>

              <!-- Progress Bar -->
              <progress 
                class="progress w-full h-3" 
                :value="calcularProgresso(meta)" 
                max="100"
                :style="{ 
                  accentColor: meta.cor
                }"
              ></progress>

              <!-- Percentual -->
              <p class="text-xs text-gray-500 mt-2">
                {{ calcularProgresso(meta).toFixed(1) }}% completo
              </p>
            </div>

            <!-- Falta -->
            <div v-if="!meta.concluida" class="alert alert-info mb-4 py-2">
              <div>
                <p class="text-sm">Faltam: <strong>{{ formatarMoeda(meta.valor_alvo - meta.valor_atual) }}</strong></p>
              </div>
            </div>

            <!-- Ações -->
            <div class="card-actions justify-end pt-4 border-t">
              <button
                @click="editarMeta(meta.id)"
                class="btn btn-sm btn-ghost"
              >
                ✏️ Editar
              </button>
              <button
                @click="abrirModalDelete(meta)"
                class="btn btn-sm btn-ghost text-error"
              >
                🗑️ Deletar
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Contador -->
      <div class="text-center mt-8 text-gray-500">
        {{ metasFiltradas.length }} meta(s) encontrada(s)
      </div>
    </div>
    <!-- Modal de Confirmação de Deleção -->
    <div
      v-if="mostraModalDelete"
      class="modal modal-open"
    >
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">
          🗑️ Excluir Meta
        </h3>
        <p class="py-4 text-gray-600">
          Tem certeza que deseja excluir a meta <strong>"{{ metaADeletar?.nome }}"</strong>?
        </p>
        <p class="text-sm text-gray-500 mb-4">
          Saldo atual: <strong>{{ formatarMoeda(metaADeletar?.valor_atual || 0) }}</strong>
        </p>
        <p class="text-sm text-error font-semibold">
          ⚠️ Esta ação não pode ser desfeita!
        </p>

        <div class="modal-action gap-2 mt-6">
          <button
            @click="fecharModalDelete"
            class="btn btn-ghost"
          >
            Cancelar
          </button>
          <button
            @click="deletarMeta"
            class="btn btn-error"
          >
            Excluir Conta
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