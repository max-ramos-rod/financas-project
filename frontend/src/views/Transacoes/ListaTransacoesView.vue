<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import type { Transacao } from '@/types'
import { parseDate, formatDateForInput } from '@/utils/date'
import { valorEfetivo, formatarMoeda, formatarCompacto } from '@/utils/financeiro'
import { useTransacoesFiltros } from '@/composables/useTransacoesFiltros'
import { useContasStore } from '@/stores/contas'
import { useCategoriasStore } from '@/stores/categorias'
import { TransacoesLoadControl } from './transacoesLoadControl'
import { buscarTransacoesFiltradas } from './transacoesFetch'
import { LABELS } from '@/utils/strings'
import ConfirmModal from '@/components/ConfirmModal.vue'
import TransacoesFiltroBarra from '@/components/Transacoes/TransacoesFiltroBarra.vue'
import TransacoesLista from '@/components/Transacoes/TransacoesLista.vue'

const router = useRouter()
const loading = ref(true)
const duplicandoId = ref<number | null>(null)
const transacoes = ref<Transacao[]>([])
const loadControl = new TransacoesLoadControl()

const contasStore = useContasStore()
const categoriasStore = useCategoriasStore()
const { contas } = storeToRefs(contasStore)
const { categorias } = storeToRefs(categoriasStore)

const {
  filtros,
  labelPeriodoAtual,
  temFiltrosAtivos,
  aplicarFiltrosDaQuery,
  queryAtualDosFiltros,
  limparFiltros,
} = useTransacoesFiltros()

const transacoesFiltradas = computed(() =>
  [...transacoes.value].sort((a, b) => {
    const byDate = parseDate(b.data).getTime() - parseDate(a.data).getTime()
    if (byDate !== 0) return byDate
    return b.id - a.id
  })
)

const contadores = computed(() => ({
  todas: transacoesFiltradas.value.length,
  entrada: transacoesFiltradas.value.filter((t) => t.tipo === 'entrada').length,
  saida: transacoesFiltradas.value.filter((t) => t.tipo === 'saida').length,
}))

const isContaCartaoCredito = (contaId: number) =>
  contas.value.find((c) => c.id === contaId)?.tipo === 'cartao_credito'

const totais = computed(() => {
  const emAberto = (t: Transacao) => {
    const s = t.status_liquidacao || 'liquidado'
    return s === 'previsto' || s === 'atrasado'
  }
  const liquidado = transacoesFiltradas.value.filter(
    (t) => (t.status_liquidacao || 'liquidado') === 'liquidado'
  )
  const entradasLiquidadas = liquidado
    .filter((t) => t.tipo === 'entrada')
    .reduce((sum, t) => sum + valorEfetivo(t), 0)
  const saidasLiquidadas = liquidado
    .filter((t) => t.tipo === 'saida')
    .reduce((sum, t) => sum + valorEfetivo(t), 0)
  const aReceber = transacoesFiltradas.value
    .filter((t) => t.tipo === 'entrada' && emAberto(t))
    .reduce((sum, t) => sum + valorEfetivo(t), 0)
  const aPagar = transacoesFiltradas.value
    .filter((t) => t.tipo === 'saida' && emAberto(t) && !isContaCartaoCredito(t.conta_id))
    .reduce((sum, t) => sum + valorEfetivo(t), 0)
  const faturaCartaoEmAberto = transacoesFiltradas.value
    .filter((t) => t.tipo === 'saida' && emAberto(t) && isContaCartaoCredito(t.conta_id))
    .reduce((sum, t) => sum + valorEfetivo(t), 0)
  const saldoProjetado =
    entradasLiquidadas + aReceber - saidasLiquidadas - aPagar - faturaCartaoEmAberto
  return { entradasLiquidadas, saidasLiquidadas, aReceber, aPagar, faturaCartaoEmAberto, saldoProjetado }
})

const fetchApoio = async () => {
  await Promise.all([contasStore.fetchContas(), categoriasStore.fetchCategorias()])
}

const fetchTransacoes = async () => {
  transacoes.value = (await buscarTransacoesFiltradas(api, { ...filtros.value })) as Transacao[]
}

const novaTransacao = () =>
  router.push({ path: '/transacoes/nova', query: queryAtualDosFiltros() })

const editarTransacao = (id: number) =>
  router.push({ path: `/transacoes/${id}/editar`, query: queryAtualDosFiltros() })

const exportandoCsv = ref(false)
const exportarCsv = async () => {
  exportandoCsv.value = true
  try {
    const params: Record<string, string> = {}
    const f = filtros.value
    if (f.tipo !== 'todas') params.tipo = f.tipo
    if (f.status_liquidacao !== 'todos') params.status_liquidacao = f.status_liquidacao
    if (f.fixa !== 'todas') params.fixa = f.fixa
    if (f.conta_id != null) params.conta_id = String(f.conta_id)
    if (f.categoria_id != null) params.categoria_id = String(f.categoria_id)
    if (f.mes) params.mes = String(f.mes)
    if (f.ano) params.ano = String(f.ano)
    if (f.busca.trim()) params.busca = f.busca.trim()

    const res = await api.get('/transacoes/export', { params, responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data as BlobPart], { type: 'text/csv' }))
    const a = document.createElement('a')
    a.href = url
    a.download =
      `transacoes_${f.ano || ''}_${f.mes ? String(f.mes).padStart(2, '0') : ''}.csv`
        .replace(/__+/g, '_')
        .replace(/_$/, '') + '.csv'
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exportandoCsv.value = false
  }
}

const abrirFaturaCartao = (t: Transacao) => {
  if (!t.fatura_conta_id || !t.fatura_competencia_ano || !t.fatura_competencia_mes) return
  router.push({
    path: `/contas/${t.fatura_conta_id}/fatura`,
    query: {
      ano: String(t.fatura_competencia_ano),
      mes: String(t.fatura_competencia_mes),
    },
  })
}

const duplicarTransacao = async (id: number) => {
  duplicandoId.value = id
  try {
    const res = await api.post<Transacao>(`/transacoes/${id}/duplicar`)
    await router.push({ path: `/transacoes/${res.data.id}/editar`, query: queryAtualDosFiltros() })
  } finally {
    duplicandoId.value = null
  }
}

const transacaoADeletar = ref<Transacao | null>(null)
const showDeleteModal = ref(false)
const transacaoALiquidar = ref<Transacao | null>(null)
const showLiquidarModal = ref(false)

const iniciarDelecao = (t: Transacao) => {
  transacaoADeletar.value = t
  showDeleteModal.value = true
}
const confirmarDeletar = async () => {
  if (!transacaoADeletar.value) return
  await api.delete(`/transacoes/${transacaoADeletar.value.id}`)
  await fetchTransacoes()
}

const iniciarLiquidacao = (t: Transacao) => {
  if (contas.value.find((c) => c.id === t.conta_id)?.tipo === 'cartao_credito') return
  const status = t.status_liquidacao || 'liquidado'
  const atrasada =
    status === 'atrasado' ||
    (t.data_vencimento && new Date(t.data_vencimento) < new Date(new Date().toDateString()))
  if (atrasada) {
    void router.push({ path: `/transacoes/${t.id}/editar`, query: queryAtualDosFiltros() })
    return
  }
  transacaoALiquidar.value = t
  showLiquidarModal.value = true
}
const confirmarLiquidar = async () => {
  if (!transacaoALiquidar.value) return
  await api.put(`/transacoes/${transacaoALiquidar.value.id}`, {
    status_liquidacao: 'liquidado',
    data_liquidacao: formatDateForInput(new Date()),
  })
  await fetchTransacoes()
}

watch(
  filtros,
  () => {
    void loadControl.aoAlterarFiltros({
      replaceQuery: () => router.replace({ query: queryAtualDosFiltros() }),
      fetchTransacoes,
    })
  },
  { deep: true }
)

onMounted(async () => {
  loading.value = true
  try {
    await loadControl.inicializar({ aplicarFiltrosDaQuery, fetchApoio, fetchTransacoes })
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-base-200">

    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">

      <!-- Page header -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-5 lg:mb-6">
        <div>
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight">
            {{ LABELS.transacoes }}
          </h1>
          <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-1">
            {{ transacoesFiltradas.length }}
            {{ transacoesFiltradas.length === 1 ? 'lançamento' : 'lançamentos' }}
            · {{ labelPeriodoAtual }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            class="btn btn-ghost btn-sm sm:btn-md whitespace-nowrap"
            :disabled="exportandoCsv"
            @click="exportarCsv"
          >
            <span v-if="exportandoCsv" class="loading loading-spinner loading-xs"></span>
            <span v-else>↓ CSV</span>
          </button>
          <button
            class="btn btn-ghost btn-sm sm:btn-md whitespace-nowrap"
            @click="router.push({ name: 'importar-transacoes' })"
          >
            Importar
          </button>
          <button
            class="btn btn-primary btn-sm sm:btn-md whitespace-nowrap flex-1 sm:flex-none"
            @click="novaTransacao"
          >
            {{ LABELS.nova_transacao }}
          </button>
        </div>
      </div>

      <!-- Filter bar -->
      <TransacoesFiltroBarra
        v-model:filtros="filtros"
        :contas="contas"
        :categorias="categorias"
        :contadores="contadores"
        @limpar="limparFiltros"
      />

      <!-- KPI strip -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-4">
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.entradas }}</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-success tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.entradasLiquidadas + totais.aReceber) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 leading-relaxed hidden sm:block">
              <span class="text-ok">{{ formatarCompacto(totais.entradasLiquidadas) }} recebido</span>
              <span v-if="totais.aReceber > 0"> · {{ formatarCompacto(totais.aReceber) }} a receber</span>
            </p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.saidas }}</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-error tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.saidasLiquidadas + totais.aPagar + totais.faturaCartaoEmAberto) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 leading-relaxed hidden sm:block">
              <span>{{ formatarCompacto(totais.saidasLiquidadas) }} pago</span>
              <span v-if="totais.aPagar > 0"> · {{ formatarCompacto(totais.aPagar) }} a pagar</span>
            </p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Saldo projetado</p>
            <p :class="['text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap', totais.saldoProjetado >= 0 ? 'text-success' : 'text-error']">
              {{ formatarMoeda(totais.saldoProjetado) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ totais.saldoProjetado >= 0 ? LABELS.resultado_positivo : LABELS.resultado_negativo }}
            </p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.cartao_em_aberto }}</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-error tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.faturaCartaoEmAberto) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">em aberto no cartão</p>
          </div>
        </div>
      </div>

      <!-- Transaction list -->
      <TransacoesLista
        :transacoes="transacoesFiltradas"
        :contas="contas"
        :categorias="categorias"
        :tem-filtros-ativos="temFiltrosAtivos"
        :duplicando-id="duplicandoId"
        @limpar-filtros="limparFiltros"
        @nova-transacao="novaTransacao"
        @editar-transacao="editarTransacao"
        @duplicar-transacao="duplicarTransacao"
        @iniciar-liquidacao="iniciarLiquidacao"
        @iniciar-delecao="iniciarDelecao"
        @abrir-fatura-cartao="abrirFaturaCartao"
      />

    </div>
  </div>

  <ConfirmModal
    v-model:open="showDeleteModal"
    severity="simple"
    :title="`Excluir '${transacaoADeletar?.descricao ?? ''}'?`"
    description="Esta ação não pode ser desfeita."
    confirm-label="Excluir"
    cancel-label="Cancelar"
    @confirm="confirmarDeletar"
  />

  <ConfirmModal
    v-model:open="showLiquidarModal"
    severity="simple"
    :title="`Liquidar '${transacaoALiquidar?.descricao ?? ''}'?`"
    description="A transação será marcada como paga com a data de hoje."
    confirm-label="Confirmar liquidação"
    cancel-label="Cancelar"
    @confirm="confirmarLiquidar"
  />
</template>
