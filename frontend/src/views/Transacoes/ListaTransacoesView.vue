<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import type { Categoria, Conta, Transacao } from '@/types'
import { parseDate, formatDateBR, formatDateForInput } from '@/utils/date'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const transacoes = ref<Transacao[]>([])
const contas = ref<Conta[]>([])
const categorias = ref<Categoria[]>([])

const filtrosPadrao = () => ({
  tipo: 'todas' as 'todas' | 'entrada' | 'saida',
  status_liquidacao: 'todos' as 'todos' | 'previsto' | 'liquidado' | 'atrasado' | 'cancelado',
  conta_id: null as number | null,
  categoria_id: null as number | null,
  mes: new Date().getMonth() + 1,
  ano: new Date().getFullYear(),
  busca: '',
})

const filtros = ref(filtrosPadrao())

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
      q.status_liquidacao === 'previsto' ||
      q.status_liquidacao === 'liquidado' ||
      q.status_liquidacao === 'atrasado' ||
      q.status_liquidacao === 'cancelado'
        ? q.status_liquidacao
        : 'todos',
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
  conta_id: filtros.value.conta_id != null ? String(filtros.value.conta_id) : undefined,
  categoria_id: filtros.value.categoria_id != null ? String(filtros.value.categoria_id) : undefined,
  mes: filtros.value.mes != null ? String(filtros.value.mes) : undefined,
  ano: filtros.value.ano ? String(filtros.value.ano) : undefined,
  busca: filtros.value.busca || undefined,
})

const fetchDados = async () => {
  loading.value = true
  try {
    const [transacoesRes, contasRes, categoriasRes] = await Promise.all([
      api.get('/transacoes'),
      api.get('/contas'),
      api.get('/categorias'),
    ])
    transacoes.value = transacoesRes.data
    contas.value = contasRes.data
    categorias.value = categoriasRes.data
  } finally {
    loading.value = false
  }
}

const transacoesFiltradas = computed(() => {
  let resultado = [...transacoes.value]

  if (filtros.value.tipo !== 'todas') {
    resultado = resultado.filter((t) => t.tipo === filtros.value.tipo)
  }
  if (filtros.value.status_liquidacao !== 'todos') {
    resultado = resultado.filter((t) => (t.status_liquidacao || 'liquidado') === filtros.value.status_liquidacao)
  }
  if (filtros.value.conta_id) {
    resultado = resultado.filter((t) => t.conta_id === filtros.value.conta_id)
  }
  if (filtros.value.categoria_id) {
    resultado = resultado.filter((t) => t.categoria_id === filtros.value.categoria_id)
  }

  if (filtros.value.mes) {
    resultado = resultado.filter((t) => {
      const data = parseDate(t.data)
      return data.getMonth() + 1 === filtros.value.mes && data.getFullYear() === filtros.value.ano
    })
  } else if (filtros.value.ano) {
    resultado = resultado.filter((t) => parseDate(t.data).getFullYear() === filtros.value.ano)
  }

  if (filtros.value.busca) {
    const busca = filtros.value.busca.toLowerCase()
    resultado = resultado.filter((t) => t.descricao.toLowerCase().includes(busca))
  }

  return resultado.sort((a, b) => {
    const byDate = parseDate(b.data).getTime() - parseDate(a.data).getTime()
    if (byDate !== 0) return byDate
    return b.id - a.id
  })
})

const totais = computed(() => {
  const emAberto = (t: Transacao) => {
    const s = t.status_liquidacao || 'liquidado'
    return s === 'previsto' || s === 'atrasado'
  }

  const liquidado = transacoesFiltradas.value.filter((t) => (t.status_liquidacao || 'liquidado') === 'liquidado')
  const entradasLiquidadas = liquidado.filter((t) => t.tipo === 'entrada').reduce((sum, t) => sum + valorEfetivo(t), 0)
  const saidasLiquidadas = liquidado.filter((t) => t.tipo === 'saida').reduce((sum, t) => sum + valorEfetivo(t), 0)
  const saldoLiquidado = entradasLiquidadas - saidasLiquidadas

  const aReceber = transacoesFiltradas.value
    .filter((t) => t.tipo === 'entrada' && emAberto(t))
    .reduce((sum, t) => sum + valorEfetivo(t), 0)

  const aPagar = transacoesFiltradas.value
    .filter((t) => t.tipo === 'saida' && emAberto(t) && !isContaCartaoCredito(t.conta_id))
    .reduce((sum, t) => sum + valorEfetivo(t), 0)

  const faturaCartaoEmAberto = transacoesFiltradas.value
    .filter((t) => t.tipo === 'saida' && emAberto(t) && isContaCartaoCredito(t.conta_id))
    .reduce((sum, t) => sum + valorEfetivo(t), 0)

  const aPagarTotal = aPagar + faturaCartaoEmAberto
  const saldoProjetado = saldoLiquidado + aReceber - aPagarTotal

  return {
    entradasLiquidadas,
    saidasLiquidadas,
    saldoLiquidado,
    aReceber,
    aPagar,
    faturaCartaoEmAberto,
    saldoProjetado,
  }
})

const valorEfetivo = (t: Transacao) => Math.max(0, t.valor + (t.valor_multa || 0) + (t.valor_juros || 0) - (t.valor_desconto || 0))

const formatarMoeda = (valor: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)
const formatarData = (data: string) => formatDateBR(data)

const getContaNome = (id: number) => contas.value.find((c) => c.id === id)?.nome || 'Conta'
const getCategoriaNome = (id: number | null) => categorias.value.find((c) => c.id === id)?.nome || 'Sem categoria'
const isContaCartaoCredito = (contaId: number) => contas.value.find((c) => c.id === contaId)?.tipo === 'cartao_credito'
const estaAtrasada = (t: Transacao) => {
  const status = t.status_liquidacao || 'liquidado'
  if (status === 'atrasado') return true
  if (!t.data_vencimento) return false
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  const vencimento = parseDate(t.data_vencimento)
  vencimento.setHours(0, 0, 0, 0)
  return vencimento < hoje
}

const statusLabel = (t: Transacao) => {
  const s = t.status_liquidacao || 'liquidado'
  if (s === 'liquidado') return t.tipo === 'entrada' ? 'Recebido' : 'Pago'
  if (s === 'previsto') {
    if (t.tipo === 'entrada') return 'Previsto'
    return isContaCartaoCredito(t.conta_id) ? 'Fatura' : 'A pagar'
  }
  if (s === 'atrasado') return 'Atrasado'
  return 'Cancelado'
}

const statusClass = (t: Transacao) => {
  const s = t.status_liquidacao || 'liquidado'

  if (s === 'liquidado') return 'badge-success'

  if (s === 'previsto') {
    return t.tipo === 'entrada'
      ? 'badge-warning'   // A receber
      : 'badge-warning'   // A pagar
  }

  if (s === 'atrasado') return 'badge-error'

  return 'badge-ghost'
}


const novaTransacao = () => router.push({ path: '/transacoes/nova', query: queryAtualDosFiltros() })
const editarTransacao = (id: number) => router.push({ path: `/transacoes/${id}/editar`, query: queryAtualDosFiltros() })

const deletarTransacao = async (id: number) => {
  await api.delete(`/transacoes/${id}`)
  await fetchDados()
}

const marcarComoLiquidado = async (t: Transacao) => {
  if (isContaCartaoCredito(t.conta_id)) return
  if (estaAtrasada(t)) {
    await router.push({ path: `/transacoes/${t.id}/editar`, query: queryAtualDosFiltros() })
    return
  }
  await api.put(`/transacoes/${t.id}`, {
    status_liquidacao: 'liquidado',
    data_liquidacao: formatDateForInput(new Date()),
  })
  await fetchDados()
}

const limparFiltros = () => {
  filtros.value = filtrosPadrao()
}

const setTipoAba = (tipo: 'todas' | 'entrada' | 'saida') => {
  filtros.value.tipo = tipo
}

watch(
  filtros,
  () => {
    void router.replace({ query: queryAtualDosFiltros() })
  },
  { deep: true }
)

onMounted(async () => {
  aplicarFiltrosDaQuery()
  await fetchDados()
})
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <div class="bg-white shadow">
      <div class="container mx-auto px-4 py-4 flex items-center justify-between">
        <h1 class="text-2xl font-bold">💸 Transacoes</h1>
        <button @click="novaTransacao" class="btn btn-primary">➕ Nova transacao</button>
      </div>
    </div>

    <div v-if="loading" class="container mx-auto px-4 py-12 text-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else class="container mx-auto px-4 py-6 space-y-6">


      <div class="card bg-white shadow">
        <div class="card-body">

          <!-- Mobile: retrátil -->
          <div class="collapse collapse-arrow md:hidden bg-base-200">
            <input type="checkbox" />
            <div class="collapse-title font-medium">
              🔎 Filtros
            </div>
            <div class="collapse-content">

              <!-- SEU GRID DE FILTROS -->
              <div class="grid grid-cols-1 gap-3">
                <input v-model="filtros.busca" class="input input-bordered lg:col-span-2" placeholder="Buscar descricao" />
                <select v-model="filtros.tipo" class="select select-bordered">
                  <option value="todas">Todos tipos</option>
                  <option value="entrada">Entradas</option>
                  <option value="saida">Saidas</option>
                </select>
                <select v-model="filtros.status_liquidacao" class="select select-bordered">
                  <option value="todos">Todos status</option>
                  <option value="liquidado">Liquidados</option>
                  <option value="previsto">Previstos</option>
                  <option value="atrasado">Atrasados</option>
                  <option value="cancelado">Cancelados</option>
                </select>
                <select v-model.number="filtros.mes" class="select select-bordered">
                  <option :value="null">Todos meses</option>
                  <option :value="1">Jan</option><option :value="2">Fev</option><option :value="3">Mar</option><option :value="4">Abr</option>
                  <option :value="5">Mai</option><option :value="6">Jun</option><option :value="7">Jul</option><option :value="8">Ago</option>
                  <option :value="9">Set</option><option :value="10">Out</option><option :value="11">Nov</option><option :value="12">Dez</option>
                </select>
                <input v-model.number="filtros.ano" type="number" class="input input-bordered" />
                <select v-model.number="filtros.conta_id" class="select select-bordered">
                  <option :value="null">Todas contas</option>
                  <option v-for="c in contas" :key="c.id" :value="c.id">{{ c.nome }}</option>
                </select>
                <select v-model.number="filtros.categoria_id" class="select select-bordered lg:col-span-2">
                  <option :value="null">Todas categorias</option>
                  <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
                </select>
              </div>

            </div>
          </div>

          <!-- Desktop: sempre aberto -->
          <div class="hidden md:block">
            <div class="flex justify-between items-center mb-3">
              <h2 class="card-title">Filtros</h2>
              <button @click="limparFiltros" class="btn btn-ghost btn-sm">Limpar</button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <input v-model="filtros.busca" class="input input-bordered lg:col-span-2" placeholder="Buscar descricao" />
              <select v-model="filtros.tipo" class="select select-bordered">
                <option value="todas">Todos tipos</option>
                <option value="entrada">Entradas</option>
                <option value="saida">Saidas</option>
              </select>
              <select v-model="filtros.status_liquidacao" class="select select-bordered">
                <option value="todos">Todos status</option>
                <option value="liquidado">Liquidados</option>
                <option value="previsto">Previstos</option>
                <option value="atrasado">Atrasados</option>
                <option value="cancelado">Cancelados</option>
              </select>
              <select v-model.number="filtros.mes" class="select select-bordered">
                <option :value="null">Todos meses</option>
                <option :value="1">Jan</option><option :value="2">Fev</option><option :value="3">Mar</option><option :value="4">Abr</option>
                <option :value="5">Mai</option><option :value="6">Jun</option><option :value="7">Jul</option><option :value="8">Ago</option>
                <option :value="9">Set</option><option :value="10">Out</option><option :value="11">Nov</option><option :value="12">Dez</option>
              </select>
              <input v-model.number="filtros.ano" type="number" class="input input-bordered" />
              <select v-model.number="filtros.conta_id" class="select select-bordered">
                <option :value="null">Todas contas</option>
                <option v-for="c in contas" :key="c.id" :value="c.id">{{ c.nome }}</option>
              </select>
              <select v-model.number="filtros.categoria_id" class="select select-bordered lg:col-span-2">
                <option :value="null">Todas categorias</option>
                <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
              </select>
            </div>
          </div>

        </div>
      </div>
      

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

        <!-- ===== PRIMEIRA LINHA ===== -->

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">Recebidas</p>
            <p class="text-3xl text-success font-bold">
              {{ formatarMoeda(totais.entradasLiquidadas) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">A receber</p>
            <p class="text-3xl text-warning font-medium">
              {{ formatarMoeda(totais.aReceber) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">Total das Entradas</p>
            <p class="text-3xl font-bold">
              {{ formatarMoeda(totais.entradasLiquidadas + totais.aReceber) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">Fatura cartão</p>
            <p class="text-3xl text-error font-bold">
              {{ formatarMoeda(totais.faturaCartaoEmAberto) }}
            </p>
          </div>
        </div>

        <!-- ===== SEGUNDA LINHA ===== -->

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">Pagas</p>
            <p class="text-3xl text-base-content">
              {{ formatarMoeda(totais.saidasLiquidadas) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">A pagar</p>
            <p class="text-3xl text-warning font-bold">
              {{ formatarMoeda(totais.aPagar) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">Total das Saídas</p>
            <p class="text-3xl font-bold">
              {{ formatarMoeda(totais.saidasLiquidadas + totais.aPagar) }}
            </p>
          </div>
        </div>

        <div class="card bg-white shadow-md">
          <div class="card-body">
            <p class="text-xs opacity-70 uppercase">Saldo Projetado</p>
              <p :class="[
                'text-3xl font-bold',
                totais.saldoProjetado >= 0 ? 'text-success' : 'text-error'
              ]">
                {{ formatarMoeda(totais.saldoProjetado) }}
              </p>
          </div>
        </div>

      </div>

      <div class="card bg-white shadow">
        <div class="card-body">
          <div class="flex items-center justify-between mb-4">
            <h2 class="card-title">Lista de transacoes</h2>
            <div role="tablist" class="tabs tabs-boxed">
              <a role="tab" class="tab" :class="{ 'tab-active': filtros.tipo === 'todas' }" @click="setTipoAba('todas')">Todas</a>
              <a role="tab" class="tab" :class="{ 'tab-active': filtros.tipo === 'entrada' }" @click="setTipoAba('entrada')">Entradas</a>
              <a role="tab" class="tab" :class="{ 'tab-active': filtros.tipo === 'saida' }" @click="setTipoAba('saida')">Saidas</a>
            </div>
          </div>
          <div v-if="transacoesFiltradas.length === 0" class="text-center py-16">
            <div class="text-6xl mb-4">📭</div>
            <p class="text-3xl font-semibold mb-2">Nenhuma transacao encontrada</p>
            <p class="text-gray-500 mb-6">
              Ajuste os filtros ou adicione uma nova transacao.
            </p>
            <button @click="novaTransacao" class="btn btn-primary">
              Nova transacao
            </button>
          </div>
          <div v-else class="space-y-2">

            <div
              v-for="t in transacoesFiltradas"
              :key="t.id"
              class="bg-base-100 rounded-xl p-4 hover:bg-base-200 transition-colors flex items-center justify-between gap-4"
            >
              <div>
                <!-- Descricao + tipo -->
                <div class="flex items-center gap-2">
                  <span
                    :class="[
                      'badge badge-sm badge-outline px-3 py-2 font-medium',
                      t.tipo === 'entrada' ? 'badge-success' : 'badge-error'
                    ]"
                  >
                    {{ t.tipo === 'entrada' ? 'Entrada' : 'Saida' }}
                  </span>
                  <p class="font-medium">
                    {{ t.descricao }}
                  </p>
                </div>

                <!-- Conta / categoria -->
                <p class="text-xs opacity-50">
                  {{ getContaNome(t.conta_id) }} • {{ getCategoriaNome(t.categoria_id) }}
                </p>

                <!-- Datas -->
                <p class="text-xs opacity-50">
                  {{ formatarData(t.data) }}
                  <span v-if="t.data_vencimento">
                    • Venc. {{ formatarData(t.data_vencimento) }}
                  </span>
                </p>

                <!-- Status -->
                <div class="mt-1">
                  <span :class="['badge badge-sm badge-outline', statusClass(t)]">{{ statusLabel(t) }}</span>
                </div>
              </div>

              <!-- Valor + ações -->
              <div class="text-right">
                <p
                  :class="[
                    'text-xl font-semibold',
                    t.tipo === 'entrada' ? 'text-success' : 'text-base-content'
                  ]"
                >
                  {{ t.tipo === 'entrada' ? '+' : '-' }}
                  {{ formatarMoeda(valorEfetivo(t)) }}
                </p>

                <div class="flex gap-1 mt-2 justify-end">

                  <div class="tooltip" data-tip="Editar">
                    <button
                      class="btn btn-ghost btn-xs opacity-70 hover:opacity-100"
                      @click="editarTransacao(t.id)"
                    >
                      ✏️
                    </button>
                  </div>

                  <div
                    v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id)"
                    class="tooltip"
                    data-tip="Liquidar"
                  >
                    <button
                      class="btn btn-ghost btn-xs text-success opacity-70 hover:opacity-100"
                      @click="marcarComoLiquidado(t)"
                    >
                      ✔
                    </button>
                  </div>

                  <div class="tooltip" data-tip="Excluir">
                    <button
                      class="btn btn-ghost btn-xs text-error opacity-40 hover:opacity-80"
                      @click="deletarTransacao(t.id)"
                    >
                      🗑
                    </button>
                  </div>

                </div>


              </div>
            </div>

          </div>

        </div>
      </div>
    </div>
  </div>
</template>









