<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import type { Meta } from '@/types'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Target } from '@lucide/vue'
import { useMetasStore } from '@/stores/metas'

const router = useRouter()
const metasStore = useMetasStore()
const { metas, loading } = storeToRefs(metasStore)
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

const filtros = ref({
  status: 'todas' as 'todas' | 'ativas' | 'concluidas',
  busca: '',
})

const metasFiltradas = computed(() => {
  let resultado = [...metas.value]
  if (filtros.value.status === 'ativas') resultado = resultado.filter(m => !m.concluida)
  else if (filtros.value.status === 'concluidas') resultado = resultado.filter(m => m.concluida)
  if (filtros.value.busca) {
    const busca = filtros.value.busca.toLowerCase()
    resultado = resultado.filter(m =>
      m.nome.toLowerCase().includes(busca) ||
      (m.descricao && m.descricao.toLowerCase().includes(busca))
    )
  }
  resultado.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  return resultado
})

const totais = computed(() => ({
  ativas: metas.value.filter(m => !m.concluida).length,
  concluidas: metas.value.filter(m => m.concluida).length,
  total: metas.value.length,
  valorAcumulado: metas.value.filter(m => !m.concluida).reduce((s, m) => s + m.valor_atual, 0),
  valorAlvo: metas.value.filter(m => !m.concluida).reduce((s, m) => s + m.valor_alvo, 0),
}))

const temFiltrosAtivos = computed(() =>
  filtros.value.status !== 'todas' || filtros.value.busca !== ''
)

const fetchDados = () => metasStore.fetchMetas()

const novaMeta = () => router.push('/metas/nova')
const editarMeta = (id: number) => router.push(`/metas/${id}/editar`)

const abrirModalDelete = (meta: Meta) => { metaADeletar.value = meta; mostraModalDelete.value = true }
const deletarMeta = async () => {
  if (!metaADeletar.value) return
  const id = metaADeletar.value.id
  try {
    await api.delete(`/metas/${id}`)
    metas.value = metas.value.filter(m => m.id !== id)
  } catch (error) {
    errorMessages.value = formatApiError(error)
    showErrorModal.value = true
  }
}

const limparFiltros = () => { filtros.value = { status: 'todas', busca: '' } }

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarData = (data: string) =>
  new Date(data).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })

const calcularProgresso = (meta: Meta) =>
  Math.min(100, (meta.valor_atual / meta.valor_alvo) * 100)

onMounted(fetchDados)
</script>

<template>
  <div class="min-h-screen bg-base-200">

    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">

      <!-- 1. Cabeçalho -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-5 lg:mb-6">
        <div>
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight">
            Metas
          </h1>
          <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-1">
            {{ metasFiltradas.length }}
            {{ metasFiltradas.length === 1 ? 'meta' : 'metas' }}
            <template v-if="temFiltrosAtivos"> · filtradas</template>
          </p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-primary btn-sm sm:btn-md whitespace-nowrap" @click="novaMeta">
            Nova Meta
          </button>
        </div>
      </div>

      <!-- 2. Toolbar de filtros -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-3 sm:p-4 gap-0">
          <div class="flex flex-wrap items-center gap-2">
            <!-- Busca -->
            <div class="relative flex-1 min-w-[180px]">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/30 text-sm">⌕</span>
              <input
                v-model="filtros.busca"
                type="search"
                class="input input-bordered input-sm w-full pl-8"
                placeholder="Buscar por nome ou descrição…"
              />
            </div>

            <!-- Segmented status -->
            <div class="join">
              <button
                class="join-item btn btn-sm"
                :class="filtros.status === 'todas' ? 'btn-primary' : 'btn-ghost border border-base-300'"
                @click="filtros.status = 'todas'"
              >
                Todas
                <span class="font-mono text-[10px] opacity-60">{{ totais.total }}</span>
              </button>
              <button
                class="join-item btn btn-sm"
                :class="filtros.status === 'ativas' ? 'btn-warning' : 'btn-ghost border border-base-300'"
                @click="filtros.status = 'ativas'"
              >
                Ativas
                <span class="font-mono text-[10px] opacity-60">{{ totais.ativas }}</span>
              </button>
              <button
                class="join-item btn btn-sm"
                :class="filtros.status === 'concluidas' ? 'btn-success' : 'btn-ghost border border-base-300'"
                @click="filtros.status = 'concluidas'"
              >
                Concluídas
                <span class="font-mono text-[10px] opacity-60">{{ totais.concluidas }}</span>
              </button>
            </div>

            <button
              v-if="temFiltrosAtivos"
              class="btn btn-ghost btn-sm text-error hidden sm:flex"
              @click="limparFiltros"
            >
              Limpar
            </button>
          </div>
        </div>
      </div>

      <!-- 3. KPI strip -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-4">
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Total</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums">{{ totais.total }}</p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">metas cadastradas</p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Ativas</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-warning tabular-nums">{{ totais.ativas }}</p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">em andamento</p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Concluídas</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-success tabular-nums">{{ totais.concluidas }}</p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">finalizadas</p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Acumulado</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-success tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.valorAcumulado) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              de {{ formatarMoeda(totais.valorAlvo) }}
            </p>
          </div>
        </div>
      </div>

      <!-- 4. Cards de metas -->
      <div v-if="metasFiltradas.length === 0" class="card bg-base-100 shadow-sm">
        <div class="card-body py-12">
          <EmptyState
            v-if="temFiltrosAtivos"
            variant="filtered"
            title="Nenhuma meta encontrada."
            description="Tente ajustar os filtros para ver mais resultados."
          >
            <template #icon><Target /></template>
            <template #actions>
              <button class="btn btn-ghost btn-sm" @click="limparFiltros">Limpar filtros</button>
            </template>
          </EmptyState>
          <EmptyState
            v-else
            variant="first-time"
            title="Nenhuma meta ainda."
            description="Crie metas financeiras para acompanhar seu progresso de poupança."
          >
            <template #icon><Target /></template>
            <template #actions>
              <button class="btn btn-primary btn-sm" @click="novaMeta">Nova Meta</button>
            </template>
          </EmptyState>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="meta in metasFiltradas"
          :key="meta.id"
          class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow"
          :style="{ borderTop: `3px solid ${meta.cor}` }"
        >
          <div class="card-body p-5 gap-3">
            <!-- Header -->
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <h3 class="font-semibold text-base truncate">{{ meta.nome }}</h3>
                <p v-if="meta.descricao" class="text-xs text-base-content/50 mt-0.5 line-clamp-1">
                  {{ meta.descricao }}
                </p>
              </div>
              <span v-if="meta.concluida" class="badge badge-success badge-sm shrink-0">Concluída</span>
              <span v-else class="badge badge-warning badge-sm shrink-0">Ativa</span>
            </div>

            <!-- Datas -->
            <div class="flex justify-between text-xs text-base-content/40 font-mono">
              <span>{{ formatarData(meta.data_inicio) }}</span>
              <span v-if="meta.data_fim">até {{ formatarData(meta.data_fim) }}</span>
            </div>

            <!-- Progresso -->
            <div>
              <div class="flex justify-between items-center mb-1.5">
                <span class="text-xs font-mono text-base-content/50 uppercase tracking-wide">Progresso</span>
                <span class="text-xs font-semibold tabular-nums">
                  {{ calcularProgresso(meta).toFixed(1) }}%
                </span>
              </div>
              <div class="h-2 w-full rounded-full bg-base-200 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :style="{ width: `${calcularProgresso(meta)}%`, background: meta.cor }"
                ></div>
              </div>
              <div class="flex justify-between mt-1.5 text-xs tabular-nums">
                <span class="text-base-content/70">{{ formatarMoeda(meta.valor_atual) }}</span>
                <span class="text-base-content/40">{{ formatarMoeda(meta.valor_alvo) }}</span>
              </div>
            </div>

            <!-- Falta (só para ativas) -->
            <div v-if="!meta.concluida" class="rounded-lg bg-base-200 px-3 py-2">
              <p class="text-xs text-base-content/60">
                Faltam
                <strong class="tabular-nums text-base-content">
                  {{ formatarMoeda(meta.valor_alvo - meta.valor_atual) }}
                </strong>
              </p>
            </div>

            <!-- Ações -->
            <div class="flex gap-1 justify-end pt-1 border-t border-base-200">
              <button class="btn btn-ghost btn-xs" @click="editarMeta(meta.id)">Editar</button>
              <button class="btn btn-ghost btn-xs text-error" @click="abrirModalDelete(meta)">Deletar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Rodapé contador -->
      <div v-if="metasFiltradas.length > 0" class="text-center mt-6">
        <span class="font-mono text-[11px] text-base-content/40">
          {{ metasFiltradas.length }} {{ metasFiltradas.length === 1 ? 'meta' : 'metas' }} exibida(s)
        </span>
        <button
          v-if="temFiltrosAtivos"
          class="btn btn-ghost btn-xs text-error ml-3 sm:hidden"
          @click="limparFiltros"
        >
          Limpar filtros
        </button>
      </div>

    </div>
  </div>

  <ConfirmModal
    v-model:open="mostraModalDelete"
    severity="simple"
    :title="`Excluir a meta '${metaADeletar?.nome ?? ''}'?`"
    :description="`Saldo acumulado de ${formatarMoeda(metaADeletar?.valor_atual ?? 0)} será descartado. Esta ação não pode ser desfeita.`"
    confirm-label="Excluir meta"
    cancel-label="Cancelar"
    @confirm="deletarMeta"
  />

  <div v-if="showErrorModal" class="modal modal-open">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">Erro</h3>
      <div class="space-y-2 text-sm text-base-content/70">
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
</template>
