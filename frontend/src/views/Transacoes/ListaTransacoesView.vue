<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import type { Categoria, Conta, Transacao } from '@/types'
import { parseDate, formatDateBR, formatDateForInput } from '@/utils/date'
import { TransacoesLoadControl } from './transacoesLoadControl'
import { buscarTransacoesFiltradas, type FiltrosTransacoes } from './transacoesFetch'
import { LABELS } from '@/utils/strings'
import EmptyState from '@/components/EmptyState.vue'
import ConfirmModal from '@/components/ConfirmModal.vue'
import { List, Filter } from '@lucide/vue'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const duplicandoId = ref<number | null>(null)
const transacoes = ref<Transacao[]>([])
const contas = ref<Conta[]>([])
const categorias = ref<Categoria[]>([])
const loadControl = new TransacoesLoadControl()

// Toggle de "Mais filtros"
const mostrarMaisFiltros = ref(false)

const nomesMesesAbrev = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

const filtrosPadrao = () => ({
  tipo: 'todas' as 'todas' | 'entrada' | 'saida',
  status_liquidacao: 'todos' as 'todos' | 'previsto' | 'liquidado' | 'atrasado' | 'cancelado',
  fixa: 'todas' as 'todas' | 'fixas' | 'nao_fixas',
  orcamento: 'todos' as 'todos' | 'fora' | 'dentro',
  valor_modo: 'todos' as 'todos' | 'igual' | 'gte' | 'lte',
  valor_ref: '',
  conta_id: null as number | null,
  categoria_id: null as number | null,
  mes: new Date().getMonth() + 1,
  ano: new Date().getFullYear(),
  busca: '',
})

const filtros = ref(filtrosPadrao())

// Período combinado (mês + ano em um único select)
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

const labelPeriodoAtual = computed(() => {
  const m = filtros.value.mes
  const a = filtros.value.ano
  if (!m) return `${a}`
  return `${nomesMesesAbrev[m - 1]} ${a}`
})

const qtdFiltrosSecundarios = computed(() => {
  const f = filtros.value
  const d = filtrosPadrao()
  return [
    f.status_liquidacao !== d.status_liquidacao,
    f.fixa !== d.fixa,
    f.orcamento !== d.orcamento,
    f.valor_modo !== d.valor_modo,
    f.conta_id !== d.conta_id,
    f.categoria_id !== d.categoria_id,
  ].filter(Boolean).length
})

const parseNumberQuery = (value: unknown): number | null => {
  if (typeof value !== 'string' || value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const aplicarFiltrosDaQuery = () => {
  const q = route.query
  const anoAtual = new Date().getFullYear()
  const mesAtual = new Date().getMonth() + 1
  filtros.value = {
    tipo: q.tipo === 'entrada' || q.tipo === 'saida' ? q.tipo : 'todas',
    status_liquidacao:
      q.status_liquidacao === 'previsto' || q.status_liquidacao === 'liquidado' ||
      q.status_liquidacao === 'atrasado' || q.status_liquidacao === 'cancelado'
        ? q.status_liquidacao : 'todos',
    fixa: q.fixa === 'fixas' || q.fixa === 'nao_fixas' ? q.fixa : 'todas',
    orcamento: q.orcamento === 'fora' || q.orcamento === 'dentro' ? q.orcamento : 'todos',
    valor_modo:
      q.valor_modo === 'igual' || q.valor_modo === 'gte' || q.valor_modo === 'lte'
        ? q.valor_modo : 'todos',
    valor_ref: typeof q.valor_ref === 'string' ? q.valor_ref : '',
    conta_id: parseNumberQuery(q.conta_id),
    categoria_id: parseNumberQuery(q.categoria_id),
    mes: parseNumberQuery(q.mes) ?? mesAtual,
    ano: parseNumberQuery(q.ano) ?? anoAtual,
    busca: typeof q.busca === 'string' ? q.busca : '',
  }
}

const queryAtualDosFiltros = () => ({
  tipo: filtros.value.tipo,
  status_liquidacao: filtros.value.status_liquidacao,
  fixa: filtros.value.fixa !== 'todas' ? filtros.value.fixa : undefined,
  orcamento: filtros.value.orcamento !== 'todos' ? filtros.value.orcamento : undefined,
  valor_modo: filtros.value.valor_modo !== 'todos' ? filtros.value.valor_modo : undefined,
  valor_ref: filtros.value.valor_ref.trim() || undefined,
  conta_id: filtros.value.conta_id != null ? String(filtros.value.conta_id) : undefined,
  categoria_id: filtros.value.categoria_id != null ? String(filtros.value.categoria_id) : undefined,
  mes: filtros.value.mes != null ? String(filtros.value.mes) : undefined,
  ano: filtros.value.ano ? String(filtros.value.ano) : undefined,
  busca: filtros.value.busca || undefined,
})

const filtrosParaApi = (): FiltrosTransacoes => ({ ...filtros.value })

const fetchApoio = async () => {
  const [contasRes, categoriasRes] = await Promise.all([
    api.get('/contas'),
    api.get('/categorias'),
  ])
  contas.value = contasRes.data
  categorias.value = categoriasRes.data
}

const fetchTransacoes = async () => {
  transacoes.value = (await buscarTransacoesFiltradas(api, filtrosParaApi())) as Transacao[]
}

const valorEfetivo = (t: Transacao) =>
  Math.max(0, t.valor + (t.valor_multa || 0) + (t.valor_juros || 0) - (t.valor_desconto || 0))

const transacoesFiltradas = computed(() =>
  [...transacoes.value].sort((a, b) => {
    const byDate = parseDate(b.data).getTime() - parseDate(a.data).getTime()
    if (byDate !== 0) return byDate
    return b.id - a.id
  })
)

const contadores = computed(() => ({
  todas: transacoesFiltradas.value.length,
  entrada: transacoesFiltradas.value.filter(t => t.tipo === 'entrada').length,
  saida: transacoesFiltradas.value.filter(t => t.tipo === 'saida').length,
}))

const totais = computed(() => {
  const emAberto = (t: Transacao) => {
    const s = t.status_liquidacao || 'liquidado'
    return s === 'previsto' || s === 'atrasado'
  }
  const liquidado = transacoesFiltradas.value.filter(t => (t.status_liquidacao || 'liquidado') === 'liquidado')
  const entradasLiquidadas = liquidado.filter(t => t.tipo === 'entrada').reduce((sum, t) => sum + valorEfetivo(t), 0)
  const saidasLiquidadas = liquidado.filter(t => t.tipo === 'saida').reduce((sum, t) => sum + valorEfetivo(t), 0)
  const aReceber = transacoesFiltradas.value.filter(t => t.tipo === 'entrada' && emAberto(t)).reduce((sum, t) => sum + valorEfetivo(t), 0)
  const aPagar = transacoesFiltradas.value.filter(t => t.tipo === 'saida' && emAberto(t) && !isContaCartaoCredito(t.conta_id)).reduce((sum, t) => sum + valorEfetivo(t), 0)
  const faturaCartaoEmAberto = transacoesFiltradas.value.filter(t => t.tipo === 'saida' && emAberto(t) && isContaCartaoCredito(t.conta_id)).reduce((sum, t) => sum + valorEfetivo(t), 0)
  const saldoProjetado = entradasLiquidadas + aReceber - saidasLiquidadas - aPagar - faturaCartaoEmAberto
  return { entradasLiquidadas, saidasLiquidadas, aReceber, aPagar, faturaCartaoEmAberto, saldoProjetado }
})

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarCompacto = (valor: number) => {
  if (valor >= 1000) {
    const k = valor / 1000
    return `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: k >= 10 ? 0 : 1 }).format(k)}k`
  }
  return formatarMoeda(valor)
}

const formatarData = (data: string) => formatDateBR(data)

const getContaNome = (id: number) => contas.value.find(c => c.id === id)?.nome || 'Conta'
const getCategoriaNome = (id: number | null) => categorias.value.find(c => c.id === id)?.nome || LABELS.sem_categoria
const isContaCartaoCredito = (contaId: number) => contas.value.find(c => c.id === contaId)?.tipo === 'cartao_credito'
const isFaturaCartao = (t: Transacao) => t.item_tipo === 'fatura_cartao'
const estaAtrasada = (t: Transacao) => {
  const status = t.status_liquidacao || 'liquidado'
  if (status === 'atrasado') return true
  if (!t.data_vencimento) return false
  const hoje = new Date(); hoje.setHours(0, 0, 0, 0)
  const venc = parseDate(t.data_vencimento); venc.setHours(0, 0, 0, 0)
  return venc < hoje
}

const statusLabel = (t: Transacao) => {
  const s = t.status_liquidacao || 'liquidado'
  if (s === 'liquidado') return t.tipo === 'entrada' ? LABELS.recebido : LABELS.pago
  if (s === 'previsto') return t.tipo === 'entrada' ? LABELS.a_receber : (isContaCartaoCredito(t.conta_id) ? 'Fatura' : LABELS.a_pagar)
  if (s === 'atrasado') return LABELS.st_atrasado
  return LABELS.st_cancelado
}

const statusColor = (t: Transacao) => {
  const s = t.status_liquidacao || 'liquidado'
  if (s === 'liquidado') return 'text-ok'
  if (s === 'atrasado') return 'text-crit'
  return 'text-warn'
}

const novaTransacao = () => router.push({ path: '/transacoes/nova', query: queryAtualDosFiltros() })
const editarTransacao = (id: number) => router.push({ path: `/transacoes/${id}/editar`, query: queryAtualDosFiltros() })

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
    a.download = `transacoes_${f.ano || ''}_${f.mes ? String(f.mes).padStart(2, '0') : ''}.csv`.replace(/__+/g, '_').replace(/_$/, '') + '.csv'
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exportandoCsv.value = false
  }
}
const abrirFaturaCartao = (t: Transacao) => {
  if (!t.fatura_conta_id || !t.fatura_competencia_ano || !t.fatura_competencia_mes) return
  router.push({ path: `/contas/${t.fatura_conta_id}/fatura`, query: { ano: String(t.fatura_competencia_ano), mes: String(t.fatura_competencia_mes) } })
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

const iniciarDelecao = (t: Transacao) => { transacaoADeletar.value = t; showDeleteModal.value = true }
const confirmarDeletar = async () => {
  if (!transacaoADeletar.value) return
  await api.delete(`/transacoes/${transacaoADeletar.value.id}`)
  await fetchTransacoes()
}

const iniciarLiquidacao = (t: Transacao) => {
  if (isContaCartaoCredito(t.conta_id)) return
  if (estaAtrasada(t)) { void router.push({ path: `/transacoes/${t.id}/editar`, query: queryAtualDosFiltros() }); return }
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

const limparFiltros = () => { filtros.value = filtrosPadrao() }
const setTipoAba = (tipo: 'todas' | 'entrada' | 'saida') => { filtros.value.tipo = tipo }

const temFiltrosAtivos = computed(() => {
  const f = filtros.value; const d = filtrosPadrao()
  return f.tipo !== d.tipo || f.status_liquidacao !== d.status_liquidacao || f.busca !== d.busca ||
    f.conta_id !== d.conta_id || f.categoria_id !== d.categoria_id || f.fixa !== d.fixa || f.orcamento !== d.orcamento
})

watch(filtros, () => {
  void loadControl.aoAlterarFiltros({
    replaceQuery: () => router.replace({ query: queryAtualDosFiltros() }),
    fetchTransacoes,
  })
}, { deep: true })

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

    <!-- ======================================================= -->
    <!-- Loading                                                  -->
    <!-- ======================================================= -->
    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">

      <!-- ===================================================== -->
      <!-- 1. Page header                                        -->
      <!-- ===================================================== -->
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
          <button class="btn btn-primary btn-sm sm:btn-md whitespace-nowrap flex-1 sm:flex-none" @click="novaTransacao">
            {{ LABELS.nova_transacao }}
          </button>
        </div>
      </div>

      <!-- ===================================================== -->
      <!-- 2. Toolbar de filtros                                 -->
      <!-- ===================================================== -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-3 sm:p-4 gap-3">

          <!-- Linha principal -->
          <div class="flex flex-wrap items-center gap-2">

            <!-- Busca -->
            <div class="relative flex-1 min-w-[180px]">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/30 text-sm">⌕</span>
              <input
                v-model="filtros.busca"
                type="search"
                class="input input-bordered input-sm w-full pl-8"
                placeholder="Buscar descrição…"
              />
            </div>

            <!-- Segmented tipo (compacto) -->
            <div class="join">
              <button
                class="join-item btn btn-sm"
                :class="filtros.tipo === 'todas' ? 'btn-primary' : 'btn-ghost border border-base-300'"
                @click="setTipoAba('todas')"
              >
                Todas
                <span class="font-mono text-[10px] opacity-60">{{ contadores.todas }}</span>
              </button>
              <button
                class="join-item btn btn-sm"
                :class="filtros.tipo === 'entrada' ? 'btn-success' : 'btn-ghost border border-base-300'"
                @click="setTipoAba('entrada')"
              >
                Entradas
                <span class="font-mono text-[10px] opacity-60">{{ contadores.entrada }}</span>
              </button>
              <button
                class="join-item btn btn-sm"
                :class="filtros.tipo === 'saida' ? 'btn-error' : 'btn-ghost border border-base-300'"
                @click="setTipoAba('saida')"
              >
                Saídas
                <span class="font-mono text-[10px] opacity-60">{{ contadores.saida }}</span>
              </button>
            </div>

            <!-- Período combinado -->
            <select
              v-model="periodoSelecionado"
              class="select select-bordered select-sm w-auto min-w-[120px]"
            >
              <option v-for="op in opcoesPeriodo" :key="op.value" :value="op.value">
                {{ op.label }}
              </option>
            </select>

            <!-- Mais filtros toggle -->
            <button
              class="btn btn-ghost btn-sm gap-1"
              :class="{ 'btn-active': mostrarMaisFiltros }"
              @click="mostrarMaisFiltros = !mostrarMaisFiltros"
            >
              <Filter class="h-3.5 w-3.5" />
              Filtros
              <span
                v-if="qtdFiltrosSecundarios > 0"
                class="badge badge-primary badge-xs"
              >{{ qtdFiltrosSecundarios }}</span>
            </button>

            <!-- Limpar (só quando há filtros) -->
            <button
              v-if="temFiltrosAtivos"
              class="btn btn-ghost btn-sm text-error hidden sm:flex"
              @click="limparFiltros"
            >
              Limpar
            </button>

          </div>

          <!-- Filtros secundários (expandíveis) -->
          <div v-if="mostrarMaisFiltros" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 pt-2 border-t border-base-200">

            <!-- Status -->
            <div class="form-control">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Status</span>
              </label>
              <select v-model="filtros.status_liquidacao" class="select select-bordered select-sm w-full">
                <option value="todos">Todos</option>
                <option value="liquidado">Liquidados</option>
                <option value="previsto">Previstos</option>
                <option value="atrasado">Atrasados</option>
                <option value="cancelado">Cancelados</option>
              </select>
            </div>

            <!-- Conta -->
            <div class="form-control">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Conta</span>
              </label>
              <select v-model.number="filtros.conta_id" class="select select-bordered select-sm w-full">
                <option :value="null">Todas</option>
                <option v-for="c in contas" :key="c.id" :value="c.id">{{ c.nome }}</option>
              </select>
            </div>

            <!-- Categoria -->
            <div class="form-control">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Categoria</span>
              </label>
              <select v-model.number="filtros.categoria_id" class="select select-bordered select-sm w-full">
                <option :value="null">Todas</option>
                <option :value="-1">Sem categoria</option>
                <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
              </select>
            </div>

            <!-- Fixa / Orçamento -->
            <div class="form-control">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Recorrência</span>
              </label>
              <select v-model="filtros.fixa" class="select select-bordered select-sm w-full">
                <option value="todas">Fixas e não fixas</option>
                <option value="fixas">Apenas fixas</option>
                <option value="nao_fixas">Apenas não fixas</option>
              </select>
            </div>

            <!-- Orçamento -->
            <div class="form-control">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Orçamento</span>
              </label>
              <select v-model="filtros.orcamento" class="select select-bordered select-sm w-full">
                <option value="todos">Todos</option>
                <option value="fora">Fora do orçamento</option>
                <option value="dentro">Dentro do orçamento</option>
              </select>
            </div>

            <!-- Valor -->
            <div class="form-control sm:col-span-2">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Valor</span>
              </label>
              <div class="flex gap-2">
                <select v-model="filtros.valor_modo" class="select select-bordered select-sm w-1/2">
                  <option value="todos">Qualquer valor</option>
                  <option value="igual">Igual a</option>
                  <option value="gte">Maior ou igual</option>
                  <option value="lte">Menor ou igual</option>
                </select>
                <input
                  v-model="filtros.valor_ref"
                  class="input input-bordered input-sm w-1/2"
                  placeholder="Ex: 500,00"
                  :disabled="filtros.valor_modo === 'todos'"
                />
              </div>
            </div>

            <!-- Limpar mobile -->
            <div class="sm:hidden">
              <button v-if="temFiltrosAtivos" class="btn btn-ghost btn-sm text-error w-full" @click="limparFiltros">
                Limpar filtros
              </button>
            </div>

          </div>

        </div>
      </div>

      <!-- ===================================================== -->
      <!-- 3. KPI strip — 4 cards                               -->
      <!-- ===================================================== -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-4">

        <!-- Entradas -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">
              {{ LABELS.entradas }}
            </p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-success tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.entradasLiquidadas + totais.aReceber) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 leading-relaxed hidden sm:block">
              <span class="text-ok">{{ formatarCompacto(totais.entradasLiquidadas) }} recebido</span>
              <span v-if="totais.aReceber > 0"> · {{ formatarCompacto(totais.aReceber) }} a receber</span>
            </p>
          </div>
        </div>

        <!-- Saídas -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">
              {{ LABELS.saidas }}
            </p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-error tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.saidasLiquidadas + totais.aPagar + totais.faturaCartaoEmAberto) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 leading-relaxed hidden sm:block">
              <span>{{ formatarCompacto(totais.saidasLiquidadas) }} pago</span>
              <span v-if="totais.aPagar > 0"> · {{ formatarCompacto(totais.aPagar) }} a pagar</span>
            </p>
          </div>
        </div>

        <!-- Saldo projetado -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">
              Saldo projetado
            </p>
            <p
              :class="[
                'text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap',
                totais.saldoProjetado >= 0 ? 'text-success' : 'text-error'
              ]"
            >
              {{ formatarMoeda(totais.saldoProjetado) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ totais.saldoProjetado >= 0 ? LABELS.resultado_positivo : LABELS.resultado_negativo }}
            </p>
          </div>
        </div>

        <!-- Cartão em aberto -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">
              {{ LABELS.cartao_em_aberto }}
            </p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-error tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.faturaCartaoEmAberto) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              em aberto no cartão
            </p>
          </div>
        </div>

      </div>

      <!-- ===================================================== -->
      <!-- 4. Lista de transações                                -->
      <!-- ===================================================== -->
      <div class="card bg-base-100 shadow-sm">

        <!-- Empty state -->
        <div v-if="transacoesFiltradas.length === 0" class="card-body py-12">
          <EmptyState
            v-if="temFiltrosAtivos"
            variant="filtered"
            title="Nenhuma transação encontrada."
            description="Tente ajustar os filtros para ver mais resultados."
          >
            <template #icon><Filter /></template>
            <template #actions>
              <button class="btn btn-ghost btn-sm" @click="limparFiltros">Limpar filtros</button>
            </template>
          </EmptyState>
          <EmptyState
            v-else
            variant="first-time"
            title="Ainda nada por aqui."
            description="Sua primeira transação aparece quando você lança uma entrada, pagamento ou saldo inicial."
          >
            <template #icon><List /></template>
            <template #actions>
              <button class="btn btn-primary btn-sm" @click="novaTransacao">{{ LABELS.nova_transacao }}</button>
            </template>
          </EmptyState>
        </div>

        <template v-else>

          <!-- ------------------------------------------------- -->
          <!-- DESKTOP — tabela compacta (≥ sm)                   -->
          <!-- ------------------------------------------------- -->
          <div class="hidden sm:block overflow-x-auto">
            <table class="table table-sm w-full">
              <thead>
                <tr class="text-[10px] font-mono uppercase tracking-widest text-base-content/40 border-b border-base-200">
                  <th class="font-medium w-[72px] pl-5">Data</th>
                  <th class="font-medium">Descrição</th>
                  <th class="font-medium w-[140px] hidden lg:table-cell">Conta</th>
                  <th class="font-medium w-[120px] hidden lg:table-cell">Categoria</th>
                  <th class="font-medium w-[110px] hidden md:table-cell">Status</th>
                  <th class="font-medium text-right w-[130px] pr-5">Valor</th>
                  <th class="w-[110px] hidden lg:table-cell"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-base-200">
                <tr
                  v-for="t in transacoesFiltradas"
                  :key="t.id"
                  class="group hover:bg-base-50 transition-colors"
                >
                  <!-- Data -->
                  <td class="pl-5">
                    <span class="font-mono text-[12px] tabular-nums text-base-content/50">
                      {{ formatarData(t.data) }}
                    </span>
                  </td>

                  <!-- Descrição + badge tipo -->
                  <td class="py-3">
                    <div class="flex items-center gap-2 min-w-0">
                      <span
                        :class="[
                          'shrink-0 w-1.5 h-1.5 rounded-full',
                          isFaturaCartao(t) ? 'bg-warning' :
                          t.tipo === 'entrada' ? 'bg-success' : 'bg-error'
                        ]"
                      ></span>
                      <span class="font-medium text-sm truncate">{{ t.descricao }}</span>
                      <span v-if="t.parcelado && t.parcela_atual && t.total_parcelas" class="font-mono text-[10px] text-base-content/40 shrink-0">
                        {{ t.parcela_atual }}/{{ t.total_parcelas }}
                      </span>
                    </div>
                    <span class="block text-xs text-base-content/40 mt-0.5 lg:hidden">
                      {{ getContaNome(t.conta_id) }}
                    </span>
                  </td>

                  <!-- Conta -->
                  <td class="hidden lg:table-cell">
                    <span class="text-sm text-base-content/60 truncate block">
                      {{ isFaturaCartao(t) ? `${getContaNome(t.conta_id)} · ${t.fatura_total_itens || 0} itens` : getContaNome(t.conta_id) }}
                    </span>
                  </td>

                  <!-- Categoria -->
                  <td class="hidden lg:table-cell">
                    <span class="text-sm text-base-content/60 truncate block">
                      {{ isFaturaCartao(t) ? '—' : getCategoriaNome(t.categoria_id) }}
                    </span>
                  </td>

                  <!-- Status -->
                  <td class="hidden md:table-cell">
                    <span :class="['flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide', statusColor(t)]">
                      <span class="w-1.5 h-1.5 rounded-full bg-current shrink-0"></span>
                      {{ statusLabel(t) }}
                    </span>
                  </td>

                  <!-- Valor -->
                  <td class="text-right pr-5">
                    <span
                      :class="[
                        'font-semibold text-sm tabular-nums whitespace-nowrap',
                        t.tipo === 'entrada' ? 'text-success' : 'text-base-content'
                      ]"
                    >
                      {{ t.tipo === 'entrada' ? '+ ' : '− ' }}{{ formatarMoeda(valorEfetivo(t)).replace('R$\u00A0', '') }}
                    </span>
                    <span :class="['block text-[10px] font-mono mt-0.5 md:hidden', statusColor(t)]">
                      {{ statusLabel(t) }}
                    </span>
                  </td>

                  <!-- Ações — aparecem no hover -->
                  <td class="pr-3 hidden lg:table-cell">
                    <div class="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        v-if="isFaturaCartao(t)"
                        class="btn btn-ghost btn-xs text-primary"
                        @click="abrirFaturaCartao(t)"
                      >Fatura</button>

                      <template v-else>
                        <button class="btn btn-ghost btn-xs" @click="editarTransacao(t.id)">Editar</button>
                        <button
                          class="btn btn-ghost btn-xs"
                          :disabled="duplicandoId === t.id"
                          @click="duplicarTransacao(t.id)"
                        >
                          <span v-if="duplicandoId === t.id" class="loading loading-spinner loading-xs"></span>
                          <span v-else>Copiar</span>
                        </button>
                        <button
                          v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id)"
                          class="btn btn-ghost btn-xs text-success"
                          @click="iniciarLiquidacao(t)"
                        >OK</button>
                        <button class="btn btn-ghost btn-xs text-error" @click="iniciarDelecao(t)">×</button>
                      </template>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- ------------------------------------------------- -->
          <!-- MOBILE — tiles verticais (< sm)                    -->
          <!-- ------------------------------------------------- -->
          <div class="sm:hidden divide-y divide-base-200">
            <div
              v-for="t in transacoesFiltradas"
              :key="`m-${t.id}`"
              class="px-4 py-3 active:bg-base-200 transition-colors"
            >
              <!-- Linha 1: data + status -->
              <div class="flex items-center justify-between mb-1">
                <span class="font-mono text-[11px] tabular-nums text-base-content/40">
                  {{ formatarData(t.data) }}
                </span>
                <span :class="['flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide', statusColor(t)]">
                  <span class="w-1 h-1 rounded-full bg-current"></span>
                  {{ statusLabel(t) }}
                </span>
              </div>

              <!-- Linha 2: descrição + valor -->
              <div class="flex items-start justify-between gap-3 mb-1">
                <div class="min-w-0 flex-1 flex items-center gap-1.5">
                  <span
                    :class="[
                      'shrink-0 w-1.5 h-1.5 rounded-full mt-0.5',
                      isFaturaCartao(t) ? 'bg-warning' :
                      t.tipo === 'entrada' ? 'bg-success' : 'bg-error'
                    ]"
                  ></span>
                  <span class="font-medium text-sm truncate">{{ t.descricao }}</span>
                </div>
                <span
                  :class="[
                    'font-semibold text-sm tabular-nums whitespace-nowrap shrink-0',
                    t.tipo === 'entrada' ? 'text-success' : 'text-base-content'
                  ]"
                >
                  {{ t.tipo === 'entrada' ? '+' : '−' }} {{ formatarMoeda(valorEfetivo(t)).replace('R$\u00A0', '') }}
                </span>
              </div>

              <!-- Linha 3: conta · categoria + ações -->
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs text-base-content/40 truncate">
                  {{ getContaNome(t.conta_id) }}
                  <template v-if="!isFaturaCartao(t)"> · {{ getCategoriaNome(t.categoria_id) }}</template>
                </span>
                <div class="flex gap-1 shrink-0">
                  <button
                    v-if="isFaturaCartao(t)"
                    class="btn btn-ghost btn-xs text-primary"
                    @click="abrirFaturaCartao(t)"
                  >Fatura</button>
                  <template v-else>
                    <button class="btn btn-ghost btn-xs" @click="editarTransacao(t.id)">Editar</button>
                    <button
                      v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id)"
                      class="btn btn-ghost btn-xs text-success"
                      @click="iniciarLiquidacao(t)"
                    >OK</button>
                    <button class="btn btn-ghost btn-xs text-error" @click="iniciarDelecao(t)">×</button>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <!-- Rodapé da lista -->
          <div class="px-5 py-3 border-t border-base-200 flex justify-between items-center">
            <span class="font-mono text-[11px] text-base-content/40">
              {{ transacoesFiltradas.length }} {{ transacoesFiltradas.length === 1 ? 'lançamento' : 'lançamentos' }}
            </span>
            <button
              v-if="temFiltrosAtivos"
              class="btn btn-ghost btn-xs text-error sm:hidden"
              @click="limparFiltros"
            >
              Limpar filtros
            </button>
          </div>

        </template>
      </div>

    </div>
  </div>

  <!-- Modais -->
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