<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import type { Orcamento } from '@/types'
import { useCategoriasStore } from '@/stores/categorias'
import { useOrcamentosStore } from '@/stores/orcamentos'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { LayoutList } from '@lucide/vue'

const router = useRouter()

const loading = ref(true)
const orcamentosStore = useOrcamentosStore()
const { orcamentos } = storeToRefs(orcamentosStore)
const categoriasStore = useCategoriasStore()
const { categorias } = storeToRefs(categoriasStore)
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

const nomesMesesAbrev = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

const mesAtual = new Date().getMonth() + 1
const anoAtual = new Date().getFullYear()

const filtros = ref({ mes: mesAtual, ano: anoAtual })

const opcoesPeriodo = computed(() => {
  const hoje = new Date()
  const options = []
  for (let i = -11; i <= 2; i++) {
    const d = new Date(hoje.getFullYear(), hoje.getMonth() + i, 1)
    options.push({
      mes: d.getMonth() + 1,
      ano: d.getFullYear(),
      label: `${nomesMesesAbrev[d.getMonth()]} ${d.getFullYear()}`,
      value: `${d.getFullYear()}-${d.getMonth() + 1}`,
    })
  }
  return options.reverse()
})

const periodoSelecionado = computed({
  get: () => `${filtros.value.ano}-${filtros.value.mes}`,
  set: (val: string) => {
    const [ano, mes] = val.split('-').map(Number)
    filtros.value.ano = ano
    filtros.value.mes = mes
  },
})

const labelPeriodoAtual = computed(() =>
  `${nomesMesesAbrev[filtros.value.mes - 1]} ${filtros.value.ano}`
)

const orcamentosFiltrados = computed(() =>
  orcamentos.value.filter(o => o.mes === filtros.value.mes && o.ano === filtros.value.ano)
    .sort((a, b) => {
      const pctA = a.valor_planejado > 0 ? a.valor_gasto / a.valor_planejado : 0
      const pctB = b.valor_planejado > 0 ? b.valor_gasto / b.valor_planejado : 0
      return pctB - pctA
    })
)

const totais = computed(() => {
  const planejado = orcamentosFiltrados.value.reduce((s, o) => s + o.valor_planejado, 0)
  const gasto = orcamentosFiltrados.value.reduce((s, o) => s + o.valor_gasto, 0)
  return {
    planejado,
    gasto,
    restante: planejado - gasto,
    percentualGasto: planejado > 0 ? (gasto / planejado) * 100 : 0,
  }
})

const fetchDados = async () => {
  loading.value = true
  try {
    await Promise.all([
      orcamentosStore.fetchOrcamentos({ mes: filtros.value.mes, ano: filtros.value.ano }),
      categoriasStore.fetchCategorias(),
    ])
  } catch {
  } finally {
    loading.value = false
  }
}

const novoOrcamento = () => router.push('/orcamentos/novo')
const editarOrcamento = (id: number) => router.push(`/orcamentos/${id}/editar`)

const abrirModalDelete = (o: Orcamento) => { orcamentoADeletar.value = o; mostraModalDelete.value = true }
const deletarOrcamento = async () => {
  if (!orcamentoADeletar.value) return
  const id = orcamentoADeletar.value.id
  try {
    await api.delete(`/orcamentos/${id}`)
    orcamentosStore.orcamentos = orcamentosStore.orcamentos.filter(o => o.id !== id)
  } catch (error) {
    errorMessages.value = formatApiError(error)
    showErrorModal.value = true
  }
}

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarCompacto = (valor: number) => {
  if (valor >= 1000) {
    const k = valor / 1000
    return `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: k >= 10 ? 0 : 1 }).format(k)}k`
  }
  return formatarMoeda(valor)
}

const getCategoriaInfo = (categoriaId: number) => {
  const cat = categorias.value.find(c => c.id === categoriaId)
  return { nome: cat?.nome || 'Sem Categoria', cor: cat?.cor || '#6B7280' }
}

const percentualOrcamento = (o: Orcamento) =>
  o.valor_planejado > 0 ? (o.valor_gasto / o.valor_planejado) * 100 : 0

const percentualBarra = (o: Orcamento) =>
  Math.min(Math.max(percentualOrcamento(o), 0), 100)

watch(filtros, fetchDados, { deep: true })

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
            Orçamentos
          </h1>
          <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-1">
            {{ orcamentosFiltrados.length }}
            {{ orcamentosFiltrados.length === 1 ? 'categoria' : 'categorias' }}
            · {{ labelPeriodoAtual }}
          </p>
        </div>
        <div class="flex gap-2">
          <select
            v-model="periodoSelecionado"
            class="select select-bordered select-sm w-auto min-w-[120px]"
          >
            <option v-for="op in opcoesPeriodo" :key="op.value" :value="op.value">
              {{ op.label }}
            </option>
          </select>
          <button class="btn btn-primary btn-sm sm:btn-md whitespace-nowrap" @click="novoOrcamento">
            Novo Orçamento
          </button>
        </div>
      </div>

      <!-- 2. KPI strip -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-4">
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Planejado</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap text-base-content">
              {{ formatarMoeda(totais.planejado) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              teto do mês
            </p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Gasto</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-error tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.gasto) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ totais.percentualGasto.toFixed(0) }}% do planejado
            </p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Restante</p>
            <p
              :class="[
                'text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap',
                totais.restante >= 0 ? 'text-success' : 'text-error'
              ]"
            >
              {{ formatarMoeda(totais.restante) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ totais.restante >= 0 ? 'dentro do limite' : 'acima do limite' }}
            </p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Utilizado</p>
            <p
              :class="[
                'text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap',
                totais.percentualGasto > 100 ? 'text-error' : totais.percentualGasto > 80 ? 'text-warning' : 'text-success'
              ]"
            >
              {{ totais.percentualGasto.toFixed(1) }}%
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ formatarCompacto(totais.gasto) }} / {{ formatarCompacto(totais.planejado) }}
            </p>
          </div>
        </div>
      </div>

      <!-- 3. Lista -->
      <div class="card bg-base-100 shadow-sm">

        <!-- Empty state -->
        <div v-if="orcamentosFiltrados.length === 0" class="card-body py-12">
          <EmptyState
            variant="first-time"
            title="Nenhum orçamento para este período."
            description="Crie orçamentos por categoria para acompanhar seus gastos mensais."
          >
            <template #icon><LayoutList /></template>
            <template #actions>
              <button class="btn btn-primary btn-sm" @click="novoOrcamento">Novo Orçamento</button>
            </template>
          </EmptyState>
        </div>

        <!-- Tabela de orçamentos -->
        <template v-else>
          <div class="overflow-x-auto">
            <table class="table table-sm w-full">
              <thead>
                <tr class="text-[10px] font-mono uppercase tracking-widest text-base-content/40 border-b border-base-200">
                  <th class="font-medium pl-5 w-[200px]">Categoria</th>
                  <th class="font-medium hidden sm:table-cell">Progresso</th>
                  <th class="font-medium text-right w-[110px]">Gasto</th>
                  <th class="font-medium text-right w-[110px] hidden sm:table-cell">Planejado</th>
                  <th class="font-medium text-right w-[90px] hidden md:table-cell">Restante</th>
                  <th class="w-[90px] hidden sm:table-cell"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-base-200">
                <tr
                  v-for="o in orcamentosFiltrados"
                  :key="o.id"
                  class="group hover:bg-base-50 transition-colors"
                >
                  <!-- Categoria -->
                  <td class="pl-5 py-3">
                    <div class="flex items-center gap-2.5">
                      <span
                        class="shrink-0 w-2.5 h-2.5 rounded-full"
                        :style="{ background: getCategoriaInfo(o.categoria_id).cor }"
                      ></span>
                      <div class="min-w-0">
                        <span class="font-medium text-sm truncate block">
                          {{ getCategoriaInfo(o.categoria_id).nome }}
                        </span>
                        <!-- mobile: progresso inline -->
                        <div class="sm:hidden mt-1 w-full">
                          <div class="h-1.5 w-full rounded-full bg-base-300 overflow-hidden">
                            <div
                              class="h-full transition-all"
                              :class="o.valor_gasto > o.valor_planejado ? 'bg-error' : 'bg-success'"
                              :style="{ width: `${percentualBarra(o)}%` }"
                            ></div>
                          </div>
                          <span class="font-mono text-[10px] text-base-content/40 mt-0.5 block">
                            {{ percentualOrcamento(o).toFixed(0) }}% · {{ formatarMoeda(o.valor_planejado) }} planejado
                          </span>
                        </div>
                      </div>
                    </div>
                  </td>

                  <!-- Barra de progresso — desktop -->
                  <td class="hidden sm:table-cell py-3">
                    <div class="flex items-center gap-2">
                      <div class="h-2 flex-1 rounded-full bg-base-300 overflow-hidden min-w-[80px]">
                        <div
                          class="h-full transition-all"
                          :class="o.valor_gasto > o.valor_planejado ? 'bg-error' : 'bg-success'"
                          :style="{ width: `${percentualBarra(o)}%` }"
                        ></div>
                      </div>
                      <span
                        :class="[
                          'font-mono text-[11px] shrink-0 tabular-nums w-[36px] text-right',
                          o.valor_gasto > o.valor_planejado ? 'text-error' : 'text-base-content/50'
                        ]"
                      >
                        {{ percentualOrcamento(o).toFixed(0) }}%
                      </span>
                    </div>
                  </td>

                  <!-- Gasto -->
                  <td class="text-right py-3">
                    <span
                      :class="[
                        'font-semibold text-sm tabular-nums',
                        o.valor_gasto > o.valor_planejado ? 'text-error' : 'text-base-content'
                      ]"
                    >
                      {{ formatarMoeda(o.valor_gasto) }}
                    </span>
                  </td>

                  <!-- Planejado -->
                  <td class="hidden sm:table-cell text-right py-3">
                    <span class="text-sm tabular-nums text-base-content/60">
                      {{ formatarMoeda(o.valor_planejado) }}
                    </span>
                  </td>

                  <!-- Restante -->
                  <td class="hidden md:table-cell text-right py-3 pr-2">
                    <span
                      :class="[
                        'text-sm tabular-nums font-medium',
                        o.valor_planejado - o.valor_gasto >= 0 ? 'text-success' : 'text-error'
                      ]"
                    >
                      {{ formatarMoeda(o.valor_planejado - o.valor_gasto) }}
                    </span>
                  </td>

                  <!-- Ações -->
                  <td class="pr-3 hidden sm:table-cell">
                    <div class="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                      <button class="btn btn-ghost btn-xs" @click="editarOrcamento(o.id)">Editar</button>
                      <button class="btn btn-ghost btn-xs text-error" @click="abrirModalDelete(o)">×</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile: ações fora da tabela (botão editar/deletar por card) -->
          <div class="sm:hidden divide-y divide-base-200 border-t border-base-200">
            <div
              v-for="o in orcamentosFiltrados"
              :key="`m-${o.id}`"
              class="px-4 py-2 flex justify-end gap-1"
            >
              <button class="btn btn-ghost btn-xs" @click="editarOrcamento(o.id)">Editar</button>
              <button class="btn btn-ghost btn-xs text-error" @click="abrirModalDelete(o)">Deletar</button>
            </div>
          </div>

          <div class="px-5 py-3 border-t border-base-200">
            <span class="font-mono text-[11px] text-base-content/40">
              {{ orcamentosFiltrados.length }} {{ orcamentosFiltrados.length === 1 ? 'categoria' : 'categorias' }}
            </span>
          </div>
        </template>
      </div>

    </div>
  </div>

  <ConfirmModal
    v-model:open="mostraModalDelete"
    severity="simple"
    :title="`Excluir orçamento de '${getCategoriaInfo(orcamentoADeletar?.categoria_id ?? 0).nome}'?`"
    description="O orçamento será removido. Os lançamentos da categoria permanecem intactos."
    confirm-label="Excluir orçamento"
    cancel-label="Cancelar"
    @confirm="deletarOrcamento"
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
