<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import api from '@/services/api'
import type { Transacao, Meta, Orcamento } from '@/types'
import { parseDate } from '@/utils/date'
import { valorEfetivo as valorEfetivoTransacao, formatarMoeda } from '@/utils/financeiro'
import { LABELS } from '@/utils/strings'
import { useContasStore } from '@/stores/contas'
import { useCategoriasStore } from '@/stores/categorias'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Calendar, TrendingDown } from '@lucide/vue'

import FluxoFinanceiroChart from '@/components/charts/FluxoFinanceiroChart.vue'
import DespesasCategoriaChart from '@/components/charts/DespesasCategoriaChart.vue'
import OrcamentoComparativoChart from '@/components/charts/OrcamentoComparativoChart.vue'

const contasStore = useContasStore()
const categoriasStore = useCategoriasStore()
const { contas } = storeToRefs(contasStore)
const { categorias } = storeToRefs(categoriasStore)
const transacoes = ref<Transacao[]>([])
const metas = ref<Meta[]>([])
const orcamentos = ref<Orcamento[]>([])
const loading = ref(true)
const erro = ref('')

const mesAtual = new Date().getMonth() + 1
const anoAtual = new Date().getFullYear()
const mesOrcamentoSelecionado = ref(mesAtual)

const nomesMeses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
const nomesMesesLongos = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

const getMesAnoOffset = (mesBase: number, anoBase: number, offset: number) => {
  const data = new Date(anoBase, mesBase - 1 + offset, 1)
  return { mes: data.getMonth() + 1, ano: data.getFullYear() }
}

const transacoesMesAtual = computed(() => {
  return transacoes.value.filter(t => {
    const data = parseDate(t.data)

    return data.getMonth() + 1 === mesAtual &&
           data.getFullYear() === anoAtual &&
           t.status_liquidacao !== 'cancelado'
  })
})

const saldoTotal = computed(() =>
  contas.value
    .filter(c => c.ativa)
    .reduce((sum, c) => sum + c.saldo, 0)
)

const saldoContaCorrente = computed(() =>
  contas.value
    .filter(c => c.ativa && c.tipo === 'conta_corrente')
    .reduce((sum, c) => sum + c.saldo, 0)
)

const saldoInvestimento = computed(() =>
  contas.value
    .filter(c => c.ativa && c.tipo === 'investimento')
    .reduce((sum, c) => sum + c.saldo, 0)
)

const receitasMes = computed(() =>
  transacoesMesAtual.value
    .filter(t => t.tipo === 'entrada')
    .reduce((sum, t) => sum + t.valor, 0)
)

const despesasMes = computed(() =>
  transacoesMesAtual.value
    .filter(t => t.tipo === 'saida')
    .reduce((sum, t) => sum + t.valor, 0)
)

const saldoMes = computed(() => receitasMes.value - despesasMes.value)

// Deltas para KPIs
const qtdReceitas = computed(() =>
  transacoesMesAtual.value.filter(t => t.tipo === 'entrada').length
)
const qtdDespesas = computed(() =>
  transacoesMesAtual.value.filter(t => t.tipo === 'saida').length
)

const despesasPorCategoria = computed(() => {
  const grupos: Record<string, number> = {}

  for (const t of transacoesMesAtual.value) {
    if (t.tipo !== 'saida') continue

    const categoria = categorias.value.find(c => c.id === t.categoria_id)
    const nome = categoria?.nome ?? 'Sem Categoria'

    grupos[nome] = (grupos[nome] || 0) + t.valor
  }

  return Object.entries(grupos)
    .map(([nome, valor]) => ({ nome, valor }))
    .sort((a, b) => b.valor - a.valor)
})

const orcamentosMesSelecionado = computed(() =>
  orcamentos.value.filter(o => o.mes === mesOrcamentoSelecionado.value && o.ano === anoAtual)
)

const orcamentoComparativo = computed(() => {
  return orcamentosMesSelecionado.value
    .map((o) => {
      const gasto = transacoes.value
        .filter(
          (t) =>
            t.tipo === 'saida' &&
            t.categoria_id === o.categoria_id &&
            parseDate(t.data).getMonth() + 1 === mesOrcamentoSelecionado.value &&
            parseDate(t.data).getFullYear() === anoAtual &&
            t.status_liquidacao !== 'cancelado'
        )
        .reduce((sum, t) => sum + valorEfetivoTransacao(t), 0)

      const categoriaNome = categorias.value.find(c => c.id === o.categoria_id)?.nome || `Categoria ${o.categoria_id}`
      return {
        categoria: categoriaNome,
        planejado: o.valor_planejado,
        gasto,
        estourado: gasto > o.valor_planejado,
      }
    })
    .sort((a, b) => (b.gasto / (b.planejado || 1)) - (a.gasto / (a.planejado || 1)))
})

const orcamentosEstourados = computed(() =>
  orcamentoComparativo.value.filter(item => item.estourado)
)

const topDespesas = computed(() =>
  transacoesMesAtual.value
    .filter(t => t.tipo === 'saida')
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 5)
)

const transacoesRecentes = computed(() =>
  [...transacoes.value]
    .filter(t => t.status_liquidacao !== 'cancelado')
    .sort((a, b) => parseDate(b.data).getTime() - parseDate(a.data).getTime())
    .slice(0, 6)
)

const fluxoFinanceiroPorMes = (mes: number, ano: number) => {
  const entradas = { recebidas: 0, previstas: 0 }
  const saidas = { pagas: 0, previstas: 0, cartao: 0 }

  for (const t of transacoes.value) {
    const data = parseDate(t.data)
    if (data.getMonth() + 1 !== mes || data.getFullYear() !== ano || t.status_liquidacao === 'cancelado') continue

    const valor = t.valor

    if (t.tipo === 'entrada') {
      if (t.status_liquidacao === 'liquidado') entradas.recebidas += valor
      else entradas.previstas += valor
    }

    if (t.tipo === 'saida') {
      const conta = contas.value.find(c => c.id === t.conta_id)
      if (conta?.tipo === 'cartao_credito') {
        saidas.cartao += valor
        continue
      }
      if (t.status_liquidacao === 'liquidado') saidas.pagas += valor
      else saidas.previstas += valor
    }
  }

  return { entradas, saidas }
}

const fluxoFinanceiroComparativo = computed(() => {
  const refs = [
    getMesAnoOffset(mesAtual, anoAtual, -1),
    getMesAnoOffset(mesAtual, anoAtual, 0),
    getMesAnoOffset(mesAtual, anoAtual, 1),
  ]

  return refs.map(({ mes, ano }) => {
    const fluxo = fluxoFinanceiroPorMes(mes, ano)
    return {
      label: `${nomesMeses[mes - 1]}/${ano.toString().slice(-2)}`,
      recebidas: fluxo.entradas.recebidas,
      aReceber: fluxo.entradas.previstas,
      pagas: fluxo.saidas.pagas,
      aPagar: fluxo.saidas.previstas,
      cartao: fluxo.saidas.cartao,
    }
  })
})

const debitoFaturaAtualCartoes = computed(() =>
  contas.value
    .filter((conta) => conta.ativa && conta.tipo === 'cartao_credito')
    .reduce((sum, conta) => sum + (conta.valor_fatura_fechada || 0), 0)
)

const metasEmAndamento = computed(() =>
  metas.value.filter(m => !m.concluida)
)

const getPercentualMeta = (meta: Meta): number =>
  Math.min((meta.valor_atual / meta.valor_alvo) * 100, 100)

const formatarData = (data: string): string => {
  const d = parseDate(data)
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
}

const labelStatusTransacao = (t: Transacao): string => {
  if (t.status_liquidacao === 'liquidado') return t.tipo === 'entrada' ? LABELS.recebido : LABELS.pago
  if (t.status_liquidacao === 'atrasado') return LABELS.st_atrasado
  return LABELS.st_previsto
}

const corStatusTransacao = (t: Transacao): string => {
  if (t.status_liquidacao === 'liquidado') return 'badge-success'
  if (t.status_liquidacao === 'atrasado') return 'badge-error'
  return 'badge-warning'
}

// Subtítulos descritivos dos cards
const subtituloOrcamento = computed(() => {
  const total = orcamentoComparativo.value.length
  const estourados = orcamentosEstourados.value.length
  if (total === 0) return 'Sem planejamento neste mês'
  if (estourados === 0) return `${total} ${total === 1 ? 'categoria planejada' : 'categorias planejadas'}`
  return `${estourados} ${estourados === 1 ? 'orçamento estourado' : 'orçamentos estourados'} em ${nomesMesesLongos[mesOrcamentoSelecionado.value - 1]}`
})

const subtituloMetas = computed(() => {
  const n = metasEmAndamento.value.length
  if (n === 0) return 'Nenhuma meta em andamento'
  return `${n} ${n === 1 ? 'meta ativa' : 'metas ativas'}`
})

const subtituloCategorias = computed(() => {
  return `${nomesMesesLongos[mesAtual - 1]} · ${anoAtual}`
})

const horaAtualizacao = computed(() => {
  const agora = new Date()
  return `${nomesMesesLongos[mesAtual - 1].toLowerCase()} ${anoAtual} · atualizado às ${String(agora.getHours()).padStart(2, '0')}:${String(agora.getMinutes()).padStart(2, '0')}`
})

const fetchDados = async () => {
  loading.value = true
  erro.value = ''

  try {
    const [transacoesRes, metasRes, orcamentosRes] = await Promise.all([
      api.get('/transacoes', { params: { page: 1, page_size: 500 } }),
      api.get('/metas'),
      api.get('/orcamentos'),
      contasStore.fetchContas(),
      categoriasStore.fetchCategorias(),
    ])
    transacoes.value = (transacoesRes.data as { data: Transacao[] }).data
    metas.value = (metasRes.data as { data: Meta[] }).data
    orcamentos.value = orcamentosRes.data
  } catch {
    erro.value = 'Não foi possível carregar o painel. Verifique sua conexão e tente novamente.'
  } finally {
    loading.value = false
  }
}

onMounted(fetchDados)
</script>

<template>
  <div class="min-h-screen bg-base-200">

    <!-- Loading skeleton -->
    <div v-if="loading" class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
      <div class="skeleton h-10 w-48 mb-6 rounded"></div>
      <div class="grid grid-cols-12 gap-5">
        <div class="col-span-12 skeleton h-28 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-28 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-28 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-28 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-28 rounded-box"></div>
        <div class="col-span-12 lg:col-span-7 skeleton h-72 rounded-box"></div>
        <div class="col-span-12 lg:col-span-5 skeleton h-72 rounded-box"></div>
        <div class="col-span-12 lg:col-span-7 skeleton h-72 rounded-box"></div>
        <div class="col-span-12 lg:col-span-5 skeleton h-72 rounded-box"></div>
      </div>
    </div>

    <!-- Erro de carregamento -->
    <div v-else-if="erro" class="container mx-auto px-4 sm:px-6 lg:px-8 py-16 flex flex-col items-center gap-4">
      <div class="alert alert-error max-w-md">
        <span>{{ erro }}</span>
      </div>
      <button class="btn btn-primary btn-sm" @click="fetchDados">Tentar novamente</button>
    </div>

    <!-- Main grid -->
    <div v-else class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">

      <!-- Page header -->
      <div class="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between mb-5 lg:mb-6">
        <h1 class="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight">Visão geral</h1>
        <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40">
          {{ horaAtualizacao }}
        </p>
      </div>

      <div class="grid grid-cols-12 gap-4 lg:gap-5">

        <!-- Hero stripe -->
        <div class="col-span-12 card bg-base-100 shadow-sm">
          <div class="card-body p-5 lg:py-5">
            <!-- Mobile: stack vertical; Desktop: régua horizontal -->
            <div class="flex flex-col gap-5 xl:flex-row xl:items-center xl:gap-6">

              <!-- Saldo total + pill (mobile: pill abaixo do saldo) -->
              <div class="xl:flex-shrink-0">
                <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.saldo_total }}</p>
                <p class="text-3xl sm:text-4xl font-bold tracking-tight tabular-nums mt-0.5">
                  {{ formatarMoeda(saldoTotal) }}
                </p>
                <div
                  v-if="saldoMes !== 0"
                  :class="['inline-flex', 'badge', 'badge-sm', 'gap-1', 'font-mono', 'tabular-nums', 'text-[10px]', 'mt-2', 'xl:hidden', saldoMes >= 0 ? 'badge-success' : 'badge-error']"
                >
                  {{ saldoMes >= 0 ? '+' : '' }}{{ formatarMoeda(saldoMes) }} este mês
                </div>
              </div>

              <div class="hidden xl:block w-px h-12 bg-base-300"></div>

              <!-- Breakdown: mobile 2 colunas em grid, desktop flex -->
              <div class="grid grid-cols-2 gap-4 xl:flex xl:gap-8 pt-4 xl:pt-0 border-t xl:border-t-0 border-base-300">
                <div>
                  <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Conta corrente</p>
                  <p class="text-lg sm:text-xl font-semibold tabular-nums mt-0.5">{{ formatarMoeda(saldoContaCorrente) }}</p>
                </div>
                <div>
                  <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Investimentos</p>
                  <p class="text-lg sm:text-xl font-semibold tabular-nums mt-0.5">{{ formatarMoeda(saldoInvestimento) }}</p>
                </div>
              </div>

              <div class="hidden xl:block flex-1"></div>

              <!-- Pill desktop only -->
              <div
                v-if="saldoMes !== 0"
                :class="['hidden', 'xl:inline-flex', 'badge', 'badge-lg', 'gap-1', 'font-mono', 'tabular-nums', 'text-[11px]', 'whitespace-nowrap', saldoMes >= 0 ? 'badge-success' : 'badge-error']"
              >
                {{ saldoMes >= 0 ? '+' : '' }}{{ formatarMoeda(saldoMes) }} este mês
              </div>

              <!-- Ações: mobile fullwidth com flex 1:1, desktop auto -->
              <div class="flex gap-2 w-full xl:w-auto">
                <router-link to="/contas" class="btn btn-ghost btn-sm flex-1 xl:flex-none whitespace-nowrap">
                  Ver contas
                </router-link>
                <router-link to="/transacoes/nova" class="btn btn-primary btn-sm flex-1 xl:flex-none whitespace-nowrap">
                  {{ LABELS.nova_transacao }}
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- KPI: Receitas do mês -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4 gap-1">
            <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.receitas_do_mes }}</p>
            <p class="text-lg sm:text-xl md:text-2xl font-bold text-success tabular-nums whitespace-nowrap">{{ formatarMoeda(receitasMes) }}</p>
            <p class="text-[11px] font-mono text-base-content/40 mt-0.5">
              {{ qtdReceitas }} {{ qtdReceitas === 1 ? 'lançamento' : 'lançamentos' }}
            </p>
          </div>
        </div>

        <!-- KPI: Despesas do mês -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4 gap-1">
            <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.despesas_do_mes }}</p>
            <p class="text-lg sm:text-xl md:text-2xl font-bold text-error tabular-nums whitespace-nowrap">{{ formatarMoeda(despesasMes) }}</p>
            <p class="text-[11px] font-mono text-base-content/40 mt-0.5">
              {{ qtdDespesas }} {{ qtdDespesas === 1 ? 'lançamento' : 'lançamentos' }}
            </p>
          </div>
        </div>

        <!-- KPI: Saldo do mês -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4 gap-1">
            <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.saldo_do_mes }}</p>
            <p :class="['text-lg', 'sm:text-xl', 'md:text-2xl', 'font-bold', 'tabular-nums', 'whitespace-nowrap', saldoMes >= 0 ? 'text-success' : 'text-error']">
              {{ formatarMoeda(saldoMes) }}
            </p>
            <p class="text-[11px] font-mono text-base-content/40 mt-0.5">
              {{ saldoMes >= 0 ? LABELS.resultado_positivo : LABELS.resultado_negativo }}
            </p>
          </div>
        </div>

        <!-- KPI: Cartão em aberto -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4 gap-1">
            <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">{{ LABELS.cartao_em_aberto }}</p>
            <p class="text-lg sm:text-xl md:text-2xl font-bold text-error tabular-nums whitespace-nowrap">{{ formatarMoeda(debitoFaturaAtualCartoes) }}</p>
            <p class="text-[11px] font-mono text-base-content/40 mt-0.5">
              Próximo fechamento
            </p>
          </div>
        </div>

        <!-- Charts row 1 — Fluxo Financeiro -->
        <div class="col-span-12 lg:col-span-7 card bg-base-100 shadow-sm">
          <div class="card-body">
            <div class="flex items-start justify-between gap-4 mb-4">
              <div>
                <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">Fluxo Financeiro</p>
                <p class="text-lg font-semibold tracking-tight mt-1">Anterior, atual, próximo</p>
              </div>
              <div class="hidden md:flex gap-3 text-[11px] font-mono text-base-content/50 items-center">
                <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-sm bg-success"></span>Entradas</span>
                <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-sm bg-error"></span>Saídas</span>
              </div>
            </div>
            <FluxoFinanceiroChart :dadosMeses="fluxoFinanceiroComparativo" />
          </div>
        </div>

        <!-- Charts row 1 — Despesas por Categoria -->
        <div class="col-span-12 lg:col-span-5 card bg-base-100 shadow-sm">
          <div class="card-body">
            <div class="flex items-start justify-between gap-4 mb-4">
              <div>
                <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">Despesas por Categoria</p>
                <p class="text-lg font-semibold tracking-tight mt-1">{{ subtituloCategorias }}</p>
              </div>
              <router-link to="/relatorios" class="text-[11px] font-mono text-primary hover:underline shrink-0">
                Ver tudo →
              </router-link>
            </div>

            <EmptyState
              v-if="despesasPorCategoria.length === 0"
              variant="zero-state"
              title="Sem despesas neste mês."
              description="As categorias com maior peso aparecem aqui assim que houver lançamentos."
            >
              <template #icon><TrendingDown /></template>
            </EmptyState>

            <DespesasCategoriaChart v-else :dados="despesasPorCategoria" />
          </div>
        </div>

        <!-- Charts row 2 — Orçamento × Gasto -->
        <div class="col-span-12 lg:col-span-7 card bg-base-100 shadow-sm">
          <div class="card-body">
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between mb-4">
              <div>
                <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">Orçamento × Gasto</p>
                <p class="text-lg font-semibold tracking-tight mt-1">{{ subtituloOrcamento }}</p>
              </div>
              <div class="w-full sm:max-w-[180px]">
                <select v-model.number="mesOrcamentoSelecionado" class="select select-bordered select-sm w-full">
                  <option :value="1">Janeiro</option>
                  <option :value="2">Fevereiro</option>
                  <option :value="3">Março</option>
                  <option :value="4">Abril</option>
                  <option :value="5">Maio</option>
                  <option :value="6">Junho</option>
                  <option :value="7">Julho</option>
                  <option :value="8">Agosto</option>
                  <option :value="9">Setembro</option>
                  <option :value="10">Outubro</option>
                  <option :value="11">Novembro</option>
                  <option :value="12">Dezembro</option>
                </select>
              </div>
            </div>

            <EmptyState
              v-if="orcamentoComparativo.length === 0"
              variant="zero-state"
              title="Você ainda não planejou este mês."
              description="Crie orçamentos por categoria para acompanhar o realizado."
            >
              <template #icon><Calendar /></template>
              <template #actions>
                <router-link to="/orcamentos" class="btn btn-primary btn-sm">Ir para orçamentos</router-link>
              </template>
            </EmptyState>

            <template v-else>
              <OrcamentoComparativoChart :dados="orcamentoComparativo" />

              <div v-if="orcamentosEstourados.length" class="alert alert-warning mt-4">
                <div>
                  <p class="font-semibold">Atenção: orçamentos estourados</p>
                  <ul class="mt-2 space-y-1 text-sm">
                    <li v-for="item in orcamentosEstourados" :key="item.categoria">
                      {{ item.categoria }}: {{ formatarMoeda(item.gasto - item.planejado) }} acima do planejado
                    </li>
                  </ul>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Charts row 2 — Metas + Maiores Despesas (stacked in right column) -->
        <div class="col-span-12 lg:col-span-5 flex flex-col gap-5">

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <div class="flex items-start justify-between gap-4 mb-4">
                <div>
                  <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">Metas em andamento</p>
                  <p class="text-lg font-semibold tracking-tight mt-1">{{ subtituloMetas }}</p>
                </div>
                <router-link to="/metas" class="text-[11px] font-mono text-primary hover:underline shrink-0">
                  Gerenciar →
                </router-link>
              </div>

              <EmptyState
                v-if="metasEmAndamento.length === 0"
                variant="zero-state"
                title="Sem metas ativas."
                description="Defina o que você quer alcançar e acompanhe o progresso."
              >
                <template #actions>
                  <router-link to="/metas" class="btn btn-primary btn-sm">Criar meta</router-link>
                </template>
              </EmptyState>

              <div v-else class="space-y-4">
                <div v-for="meta in metasEmAndamento.slice(0, 3)" :key="meta.id">
                  <div class="flex justify-between items-baseline mb-1.5">
                    <span class="text-sm font-medium">{{ meta.nome }}</span>
                    <span class="text-[11px] font-mono tabular-nums text-base-content/50">
                      {{ getPercentualMeta(meta).toFixed(0) }}%
                    </span>
                  </div>
                  <div class="text-[11px] font-mono tabular-nums text-base-content/40 mb-1.5">
                    {{ formatarMoeda(meta.valor_atual) }} / {{ formatarMoeda(meta.valor_alvo) }}
                  </div>
                  <progress class="progress progress-primary w-full h-1.5" :value="getPercentualMeta(meta)" max="100"></progress>
                </div>
              </div>
            </div>
          </div>

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <div class="mb-4">
                <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">Maiores Despesas</p>
                <p class="text-lg font-semibold tracking-tight mt-1">Top 5 do mês</p>
              </div>

              <EmptyState
                v-if="topDespesas.length === 0"
                variant="filtered"
                title="Sem despesas este mês."
              >
                <template #icon><TrendingDown /></template>
                <template #actions>
                  <router-link to="/transacoes" class="btn btn-ghost btn-sm">Ver transações</router-link>
                </template>
              </EmptyState>

              <div v-else class="space-y-3">
                <div v-for="t in topDespesas" :key="t.id" class="flex justify-between gap-3 text-sm">
                  <span class="truncate text-base-content/80">{{ t.descricao }}</span>
                  <span class="whitespace-nowrap font-semibold text-error tabular-nums">
                    − {{ formatarMoeda(t.valor).replace('R$\u00A0', '') }}
                  </span>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Transações recentes (faixa cheia) -->
        <div class="col-span-12 card bg-base-100 shadow-sm">
          <div class="card-body">
            <div class="flex items-start justify-between gap-4 mb-4">
              <div>
                <p class="text-[11px] font-mono uppercase tracking-widest text-base-content/50">Transações recentes</p>
                <p class="text-lg font-semibold tracking-tight mt-1">
                  {{ transacoesRecentes.length === 0 ? 'Sem lançamentos' : `Últimos ${transacoesRecentes.length} lançamentos` }}
                </p>
              </div>
              <router-link to="/transacoes" class="text-[11px] font-mono text-primary hover:underline shrink-0">
                Ver todas →
              </router-link>
            </div>

            <EmptyState
              v-if="transacoesRecentes.length === 0"
              variant="first-time"
              title="Sua primeira transação aparece aqui."
              description="Lance uma entrada, saída ou saldo inicial para começar."
            >
              <template #actions>
                <router-link to="/transacoes/nova" class="btn btn-primary btn-sm">{{ LABELS.nova_transacao }}</router-link>
              </template>
            </EmptyState>

            <!-- Mobile: linha 1 (data, desc, valor) + linha 2 (categoria · status). Desktop: tudo em uma linha. -->
            <div v-else class="divide-y divide-base-300">
              <div
                v-for="t in transacoesRecentes"
                :key="t.id"
                class="py-3 sm:grid sm:grid-cols-[60px_1fr_auto_auto] sm:gap-4 sm:items-center text-sm"
              >
                <!-- Mobile layout -->
                <div class="flex items-start justify-between gap-3 sm:hidden">
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2">
                      <span class="text-[11px] font-mono tabular-nums text-base-content/40 shrink-0">{{ formatarData(t.data) }}</span>
                      <span :class="['badge', 'badge-xs', corStatusTransacao(t)]">
                        {{ labelStatusTransacao(t) }}
                      </span>
                    </div>
                    <p class="truncate font-medium mt-1">{{ t.descricao }}</p>
                    <p class="text-xs text-base-content/40 truncate">
                      {{ categorias.find(c => c.id === t.categoria_id)?.nome || LABELS.sem_categoria }}
                    </p>
                  </div>
                  <span
                    :class="['font-semibold', 'tabular-nums', 'whitespace-nowrap', 'shrink-0', t.tipo === 'entrada' ? 'text-success' : 'text-error']"
                  >
                    {{ t.tipo === 'entrada' ? '+ ' : '− ' }}{{ formatarMoeda(t.valor).replace('R$\u00A0', '') }}
                  </span>
                </div>

                <!-- Desktop layout -->
                <span class="hidden sm:inline text-[11px] font-mono tabular-nums text-base-content/40">{{ formatarData(t.data) }}</span>
                <div class="hidden sm:block min-w-0">
                  <p class="truncate font-medium">{{ t.descricao }}</p>
                  <p class="text-xs text-base-content/40 truncate">
                    {{ categorias.find(c => c.id === t.categoria_id)?.nome || LABELS.sem_categoria }}
                  </p>
                </div>
                <span :class="['hidden', 'sm:inline-flex', 'badge', 'badge-sm', corStatusTransacao(t)]">
                  {{ labelStatusTransacao(t) }}
                </span>
                <span
                  :class="['hidden', 'sm:inline', 'font-semibold', 'tabular-nums', 'whitespace-nowrap', t.tipo === 'entrada' ? 'text-success' : 'text-error']"
                >
                  {{ t.tipo === 'entrada' ? '+ ' : '− ' }}{{ formatarMoeda(t.valor).replace('R$\u00A0', '') }}
                </span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>