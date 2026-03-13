<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { Conta, Transacao, Meta, Categoria, Orcamento } from '@/types'
import { parseDate } from '@/utils/date'

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

const fluxoFinanceiro = computed(() => {
  const entradas = { recebidas: 0, previstas: 0 }
  const saidas = { pagas: 0, previstas: 0, cartao: 0 }

  for (const t of transacoesMesAtual.value) {
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
})

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
  fluxoFinanceiro.value.saidas.cartao
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
    <div v-if="loading" class="container mx-auto px-4 py-6 space-y-6">
      <div class="skeleton h-40 w-full rounded-box"></div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div class="skeleton h-28 rounded-box"></div>
        <div class="skeleton h-28 rounded-box"></div>
        <div class="skeleton h-28 rounded-box"></div>
        <div class="skeleton h-28 rounded-box"></div>
      </div>
      <div class="skeleton h-80 w-full rounded-box"></div>
      <div class="skeleton h-80 w-full rounded-box"></div>
      <div class="skeleton h-72 w-full rounded-box"></div>
    </div>

    <div v-else class="container mx-auto px-4 py-6 space-y-6">
      <div class="card text-white shadow-xl" style="background: linear-gradient(135deg, #7C3AED, #5B21B6)">
        <div class="card-body gap-4">
          <div class="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p class="text-sm opacity-80">Saldo Total</p>
              <p class="text-4xl font-bold tracking-tight">
                {{ formatarMoeda(saldoTotal) }}
              </p>
            </div>
            <router-link to="/transacoes/nova" class="btn btn-secondary btn-sm w-full md:w-auto">
              Nova transacao
            </router-link>
          </div>

          <div class="stats stats-vertical bg-white/10 text-white shadow-none md:stats-horizontal">
            <div class="stat px-4 py-3">
              <div class="stat-title text-white/70">Conta corrente</div>
              <div class="stat-value text-xl">{{ formatarMoeda(saldoContaCorrente) }}</div>
            </div>
            <div class="stat px-4 py-3">
              <div class="stat-title text-white/70">Investimentos</div>
              <div class="stat-value text-xl">{{ formatarMoeda(saldoInvestimento) }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="stats stats-vertical gap-4 shadow-sm lg:stats-horizontal">
        <div class="stat bg-base-100 rounded-box">
          <div class="stat-title">Receitas do mes</div>
          <div class="stat-value text-success">{{ formatarMoeda(receitasMes) }}</div>
        </div>
        <div class="stat bg-base-100 rounded-box">
          <div class="stat-title">Despesas do mes</div>
          <div class="stat-value text-error">{{ formatarMoeda(despesasMes) }}</div>
        </div>
        <div class="stat bg-base-100 rounded-box">
          <div class="stat-title">Cartao em aberto</div>
          <div class="stat-value text-error">{{ formatarMoeda(debitoFaturaAtualCartoes) }}</div>
        </div>
        <div class="stat bg-base-100 rounded-box">
          <div class="stat-title">Saldo do mes</div>
          <div :class="['stat-value', saldoMes >= 0 ? 'text-success' : 'text-error']">
            {{ formatarMoeda(saldoMes) }}
          </div>
          <div class="stat-desc">{{ saldoMes >= 0 ? 'Resultado positivo no periodo' : 'Atencao ao fluxo do periodo' }}</div>
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 class="text-sm uppercase opacity-60 tracking-wide">Fluxo Financeiro</h3>
              <p class="text-xs opacity-50">Mes anterior, atual e proximo para leitura de tendencia.</p>
            </div>
          </div>
          <FluxoFinanceiroChart :dadosMeses="fluxoFinanceiroComparativo" />
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 class="text-sm uppercase opacity-60 tracking-wide">Despesas por Categoria</h3>
              <p class="text-xs opacity-50">Categorias com maior peso no mes atual.</p>
            </div>
          </div>
          <DespesasCategoriaChart :dados="despesasPorCategoria" />
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <h3 class="text-sm uppercase opacity-60 tracking-wide">Orcamento x Gasto</h3>
              <p class="text-xs opacity-50">Compare rapidamente o planejado com o realizado.</p>
            </div>

            <div class="w-full max-w-xs">
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
          </div>

          <div v-if="orcamentoComparativo.length === 0" class="py-4 text-center text-sm opacity-50">
            Nenhum orcamento cadastrado para o mes selecionado.
          </div>

          <template v-else>
            <OrcamentoComparativoChart :dados="orcamentoComparativo" />

            <div v-if="orcamentosEstourados.length" class="alert alert-warning mt-4">
              <div>
                <p class="font-semibold">Atencao: orcamentos estourados</p>
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

      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <h3 class="mb-2 text-sm uppercase tracking-wide opacity-60">Maiores Despesas</h3>

          <div v-if="topDespesas.length === 0" class="py-4 text-center text-sm opacity-50">
            Nenhuma despesa relevante este mes
          </div>

          <div v-else class="space-y-2">
            <div v-for="t in topDespesas" :key="t.id" class="flex justify-between gap-3 text-sm">
              <span class="truncate opacity-80">{{ t.descricao }}</span>
              <span class="whitespace-nowrap font-semibold text-error">
                {{ formatarMoeda(t.valor) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="metasEmAndamento.length" class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <h3 class="text-sm uppercase opacity-60 tracking-wide">Metas Financeiras</h3>

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
    </div>
  </div>
</template>
