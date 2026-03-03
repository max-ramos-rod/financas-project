<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { Conta, Transacao, Meta, Categoria, Orcamento } from '@/types'
import { parseDate } from '@/utils/date'

import FluxoFinanceiroChart from '@/components/charts/FluxoFinanceiroChart.vue'
import DespesasCategoriaChart from '@/components/charts/DespesasCategoriaChart.vue'
import OrcamentoComparativoChart from '@/components/charts/OrcamentoComparativoChart.vue'

// State
const contas = ref<Conta[]>([])
const transacoes = ref<Transacao[]>([])
const metas = ref<Meta[]>([])
const categorias = ref<Categoria[]>([])
const orcamentos = ref<Orcamento[]>([])
const loading = ref(true)

// =========================
// 📅 MÊS ATUAL (timezone-safe)
// =========================

const mesAtual = new Date().getMonth() + 1
const anoAtual = new Date().getFullYear()
const mesOrcamentoSelecionado = ref(mesAtual)

const transacoesMesAtual = computed(() => {
  return transacoes.value.filter(t => {
    const data = parseDate(t.data)

    return data.getMonth() + 1 === mesAtual &&
           data.getFullYear() === anoAtual &&
           t.status_liquidacao !== 'cancelado'
  })
})

// =========================
// 💰 SALDOS
// =========================

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

// =========================
// 📈 RECEITAS / DESPESAS
// =========================

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

// =========================
// 📊 DESPESAS POR CATEGORIA
// =========================

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

// =========================
// 🔥 TOP DESPESAS
// =========================

const topDespesas = computed(() =>
  transacoesMesAtual.value
    .filter(t => t.tipo === 'saida')
    .sort((a, b) => b.valor - a.valor)
    .slice(0, 5)
)

// =========================
// 💥 FLUXO FINANCEIRO (core UX)
// =========================

const fluxoFinanceiro = computed(() => {
  const entradas = { recebidas: 0, previstas: 0 }
  const saidas = { pagas: 0, previstas: 0, cartao: 0 }

  for (const t of transacoesMesAtual.value) {
    const valor = t.valor

    if (t.tipo === 'entrada') {
      if (t.status_liquidacao === 'liquidado')
        entradas.recebidas += valor
      else
        entradas.previstas += valor
    }

    if (t.tipo === 'saida') {
      const conta = contas.value.find(c => c.id === t.conta_id)

      if (conta?.tipo === 'cartao_credito') {
        saidas.cartao += valor
        continue
      }

      if (t.status_liquidacao === 'liquidado')
        saidas.pagas += valor
      else
        saidas.previstas += valor
    }
  }

  return { entradas, saidas }
})

// =========================
// 💳 CARTÃO EM ABERTO
// =========================

const debitoFaturaAtualCartoes = computed(() =>
  fluxoFinanceiro.value.saidas.cartao
)

// =========================
// 🎯 METAS
// =========================

const metasEmAndamento = computed(() =>
  metas.value.filter(m => !m.concluida)
)

const getPercentualMeta = (meta: Meta): number =>
  Math.min((meta.valor_atual / meta.valor_alvo) * 100, 100)

// =========================
// 🎨 FORMATADORES
// =========================

const formatarMoeda = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)

// =========================
// 🌐 FETCH
// =========================

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

    <!-- Loading -->
    <div v-if="loading" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4 opacity-70">Carregando seu painel financeiro...</p>
    </div>

    <!-- Dashboard -->
    <div v-else class="container mx-auto px-4 py-6 space-y-6">

      <!-- SALDO DOMINANTE -->
      <div class="card text-white shadow-xl"
           style="background: linear-gradient(135deg, #7C3AED, #5B21B6)">
        <div class="card-body">

          <p class="text-sm opacity-80">Saldo Total</p>

          <p class="text-4xl font-bold tracking-tight">
            {{ formatarMoeda(saldoTotal) }}
          </p>

          <div class="flex justify-between text-xs opacity-80 mt-2">
            <span>Conta Corrente: {{ formatarMoeda(saldoContaCorrente) }}</span>
            <span>Investimentos: {{ formatarMoeda(saldoInvestimento) }}</span>
          </div>

        </div>
      </div>

      <!-- FLUXO FINANCEIRO -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">

          <h3 class="text-sm uppercase opacity-60 tracking-wide">
            Fluxo Financeiro do Mês
          </h3>

          <FluxoFinanceiroChart
            :recebidas="fluxoFinanceiro.entradas.recebidas"
            :aReceber="fluxoFinanceiro.entradas.previstas"
            :pagas="fluxoFinanceiro.saidas.pagas"
            :aPagar="fluxoFinanceiro.saidas.previstas"
            :cartao="fluxoFinanceiro.saidas.cartao"
          />

        </div>
      </div>

      <!-- DESPESAS POR CATEGORIA -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">

          <h3 class="text-sm uppercase opacity-60 tracking-wide">
            Despesas por Categoria
          </h3>

          <DespesasCategoriaChart :dados="despesasPorCategoria" />

        </div>
      </div>

      <!-- ORCAMENTO X GASTO (MES ATUAL) -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">

          <h3 class="text-sm uppercase opacity-60 tracking-wide">
            Orcamento x Gasto (Mes Atual)
          </h3>

          <div class="mt-3 mb-2 w-full max-w-xs">
            <label class="label py-1"><span class="label-text text-xs">Mes de referencia</span></label>
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

          <div v-if="orcamentoComparativo.length === 0" class="text-sm opacity-50 py-4 text-center">
            Nenhum orcamento cadastrado para o mes selecionado.
          </div>

          <template v-else>
            <OrcamentoComparativoChart :dados="orcamentoComparativo" />

            <div v-if="orcamentosEstourados.length" class="mt-4 p-3 rounded-lg bg-red-50 border border-red-200">
              <p class="text-sm font-semibold text-red-700">Atencao: orcamentos estourados</p>
              <ul class="mt-2 space-y-1 text-sm text-red-700">
                <li v-for="item in orcamentosEstourados" :key="item.categoria">
                  {{ item.categoria }}: {{ formatarMoeda(item.gasto - item.planejado) }} acima do planejado
                </li>
              </ul>
            </div>
          </template>

        </div>
      </div>

      <!-- COMPROMISSOS / ALERTAS -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <p class="text-xs opacity-60">Cartão em Aberto</p>
            <p class="text-xl font-bold text-error">
              {{ formatarMoeda(debitoFaturaAtualCartoes) }}
            </p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <p class="text-xs opacity-60">Saldo do Mês</p>
            <p :class="[
                'text-xl font-bold',
                saldoMes >= 0 ? 'text-success' : 'text-error'
            ]">
              {{ formatarMoeda(saldoMes) }}
            </p>
          </div>
        </div>

      </div>

      <!-- MAIORES DESPESAS -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">

          <h3 class="text-sm uppercase opacity-60 tracking-wide mb-2">
            Maiores Despesas
          </h3>

          <div v-if="topDespesas.length === 0"
               class="text-sm opacity-50 py-4 text-center">
            Nenhuma despesa relevante este mês
          </div>

          <div v-else class="space-y-2">
            <div v-for="t in topDespesas" :key="t.id"
                 class="flex justify-between text-sm">

              <span class="opacity-80 truncate">
                {{ t.descricao }}
              </span>

              <span class="font-semibold text-error">
                {{ formatarMoeda(t.valor) }}
              </span>

            </div>
          </div>

        </div>
      </div>

      <!-- METAS -->
      <div v-if="metasEmAndamento.length"
           class="card bg-base-100 shadow-sm">
        <div class="card-body">

          <h3 class="text-sm uppercase opacity-60 tracking-wide">
            Metas Financeiras
          </h3>

          <div class="space-y-3 mt-2">
            <div v-for="meta in metasEmAndamento.slice(0, 3)"
                 :key="meta.id">

              <div class="flex justify-between text-xs mb-1">
                <span>{{ meta.nome }}</span>
                <span>{{ getPercentualMeta(meta).toFixed(0) }}%</span>
              </div>

              <progress class="progress progress-primary w-full"
                        :value="getPercentualMeta(meta)"
                        max="100"></progress>

            </div>
          </div>

        </div>
      </div>

      <!-- AÇÕES RÁPIDAS -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">

        <router-link to="/transacoes/nova"
                     class="btn btn-primary">
          Nova
        </router-link>

        <router-link to="/transacoes"
                     class="btn btn-ghost">
          Transações
        </router-link>

        <router-link to="/relatorios"
                     class="btn btn-ghost">
          Relatórios
        </router-link>

        <router-link to="/metas"
                     class="btn btn-ghost">
          Metas
        </router-link>

      </div>

    </div>
  </div>
</template>
