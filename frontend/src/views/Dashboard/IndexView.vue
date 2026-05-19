<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { Conta, Transacao, Meta, Categoria, Orcamento } from '@/types'
import { parseDate } from '@/utils/date'
import { LABELS } from '@/utils/strings'
import EmptyState from '@/components/EmptyState.vue'
import { Calendar, TrendingDown } from '@lucide/vue'

import FluxoFinanceiroChart from '@/components/charts/FluxoFinanceiroChart.vue'
import DespesasCategoriaChart from '@/components/charts/DespesasCategoriaChart.vue'
import OrcamentoComparativoChart from '@/components/charts/OrcamentoComparativoChart.vue'

const contas = ref<Conta[]>([])
const transacoes = ref<Transacao[]>([])
const metas = ref<Meta[]>([])
const categorias = ref<Categoria[]>([])
const orcamentos = ref<Orcamento[]>([])
const loading = ref(true)

const mesAtual = new Date().getMonth() + 1
const anoAtual = new Date().getFullYear()
const mesOrcamentoSelecionado = ref(mesAtual)

const nomesMeses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

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

const valorEfetivoTransacao = (t: Transacao) =>
  Math.max(0, t.valor + (t.valor_multa || 0) + (t.valor_juros || 0) - (t.valor_desconto || 0))

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

const formatarMoeda = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)

const fetchDados = async () => {
  loading.value = true

  try {
    const [contasRes, transacoesRes, metasRes, categoriasRes, orcamentosRes] =
      await Promise.all([
        api.get('/contas'),
        api.get('/transacoes'),
        api.get('/metas'),
        api.get('/categorias'),
        api.get('/orcamentos')
      ])

    contas.value = contasRes.data
    transacoes.value = transacoesRes.data
    metas.value = metasRes.data
    categorias.value = categoriasRes.data
    orcamentos.value = orcamentosRes.data
  } catch (error) {
    console.error('Erro ao carregar dashboard:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchDados)
</script>

<template>
  <div class="min-h-screen bg-base-200">

    <!-- Loading skeleton -->
    <div v-if="loading" class="container mx-auto px-4 py-6">
      <div class="grid grid-cols-12 gap-5">
        <div class="col-span-12 skeleton h-28 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-24 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-24 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-24 rounded-box"></div>
        <div class="col-span-6 lg:col-span-3 skeleton h-24 rounded-box"></div>
        <div class="col-span-12 lg:col-span-7 skeleton h-72 rounded-box"></div>
        <div class="col-span-12 lg:col-span-5 skeleton h-72 rounded-box"></div>
        <div class="col-span-12 lg:col-span-7 skeleton h-72 rounded-box"></div>
        <div class="col-span-12 lg:col-span-5 skeleton h-72 rounded-box"></div>
      </div>
    </div>

    <!-- Main grid -->
    <div v-else class="container mx-auto px-4 py-6">
      <div class="grid grid-cols-12 gap-5">

        <!-- Hero stripe -->
        <div class="col-span-12 card bg-base-100 shadow-sm">
          <div class="card-body py-5">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-center">
              <div class="flex-shrink-0">
                <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Saldo Total</p>
                <p class="text-4xl font-bold tracking-tight tabular-nums">
                  {{ formatarMoeda(saldoTotal) }}
                </p>
              </div>

              <div class="hidden lg:block w-px h-12 bg-base-300 mx-2"></div>

              <div class="flex gap-8">
                <div>
                  <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Conta corrente</p>
                  <p class="text-xl font-semibold tabular-nums">{{ formatarMoeda(saldoContaCorrente) }}</p>
                </div>
                <div>
                  <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Investimentos</p>
                  <p class="text-xl font-semibold tabular-nums">{{ formatarMoeda(saldoInvestimento) }}</p>
                </div>
              </div>

              <div class="flex-1"></div>

              <div :class="['badge', 'badge-lg', saldoMes >= 0 ? 'badge-success' : 'badge-error', 'font-semibold', 'tabular-nums', 'gap-1']">
                {{ saldoMes >= 0 ? '+' : '' }}{{ formatarMoeda(saldoMes) }} este mês
              </div>

              <router-link to="/transacoes/nova" class="btn btn-primary btn-sm w-full lg:w-auto">
                {{ LABELS.nova_transacao }}
              </router-link>
            </div>
          </div>
        </div>

        <!-- KPI: Receitas do mês -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4">
            <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">{{ LABELS.receitas_do_mes }}</p>
            <p class="text-2xl font-bold text-success tabular-nums">{{ formatarMoeda(receitasMes) }}</p>
          </div>
        </div>

        <!-- KPI: Despesas do mês -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4">
            <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">{{ LABELS.despesas_do_mes }}</p>
            <p class="text-2xl font-bold text-error tabular-nums">{{ formatarMoeda(despesasMes) }}</p>
          </div>
        </div>

        <!-- KPI: Saldo do mês -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4">
            <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">{{ LABELS.saldo_do_mes }}</p>
            <p :class="['text-2xl', 'font-bold', 'tabular-nums', saldoMes >= 0 ? 'text-success' : 'text-error']">
              {{ formatarMoeda(saldoMes) }}
            </p>
            <p class="text-xs opacity-50 mt-1">{{ saldoMes >= 0 ? LABELS.resultado_positivo : LABELS.resultado_negativo }}</p>
          </div>
        </div>

        <!-- KPI: Cartão em aberto -->
        <div class="col-span-6 lg:col-span-3 card bg-base-100 shadow-sm">
          <div class="card-body py-4">
            <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">{{ LABELS.cartao_em_aberto }}</p>
            <p class="text-2xl font-bold text-error tabular-nums">{{ formatarMoeda(debitoFaturaAtualCartoes) }}</p>
          </div>
        </div>

        <!-- Charts row 1 — Fluxo Financeiro -->
        <div class="col-span-12 lg:col-span-7 card bg-base-100 shadow-sm">
          <div class="card-body">
            <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Fluxo Financeiro</p>
            <p class="text-xs opacity-40 mb-1">Mês anterior, atual e próximo para leitura de tendência.</p>
            <FluxoFinanceiroChart :dadosMeses="fluxoFinanceiroComparativo" />
          </div>
        </div>

        <!-- Charts row 1 — Despesas por Categoria -->
        <div class="col-span-12 lg:col-span-5 card bg-base-100 shadow-sm">
          <div class="card-body">
            <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Despesas por Categoria</p>
            <p class="text-xs opacity-40 mb-1">Categorias com maior peso no mês atual.</p>
            <DespesasCategoriaChart :dados="despesasPorCategoria" />
          </div>
        </div>

        <!-- Charts row 2 — Orçamento × Gasto -->
        <div class="col-span-12 lg:col-span-7 card bg-base-100 shadow-sm">
          <div class="card-body">
            <div class="flex flex-col gap-2 md:flex-row md:items-end md:justify-between mb-2">
              <div>
                <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Orçamento × Gasto</p>
                <p class="text-xs opacity-40">Compare o planejado com o realizado.</p>
              </div>
              <div class="w-full max-w-xs">
                <label class="label py-1"><span class="label-text text-xs">{{ LABELS.mes_de_referencia }}</span></label>
                <select v-model.number="mesOrcamentoSelecionado" class="select select-bordered select-sm w-full">
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

          <div v-if="metasEmAndamento.length" class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Metas Financeiras</p>
              <div class="mt-2 space-y-3">
                <div v-for="meta in metasEmAndamento.slice(0, 3)" :key="meta.id">
                  <div class="mb-1 flex justify-between text-xs">
                    <span>{{ meta.nome }}</span>
                    <span>{{ getPercentualMeta(meta).toFixed(0) }}%</span>
                  </div>
                  <progress class="progress progress-primary w-full" :value="getPercentualMeta(meta)" max="100"></progress>
                </div>
              </div>
            </div>
          </div>

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <p class="text-[11px] font-mono uppercase tracking-widest opacity-50">Maiores Despesas</p>

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

              <div v-else class="mt-2 space-y-2">
                <div v-for="t in topDespesas" :key="t.id" class="flex justify-between gap-3 text-sm">
                  <span class="truncate opacity-80">{{ t.descricao }}</span>
                  <span class="whitespace-nowrap font-semibold text-error tabular-nums">
                    {{ formatarMoeda(t.valor) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  </div>
</template>
