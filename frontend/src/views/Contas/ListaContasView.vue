<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import type { Conta } from '@/types'
import { formatDateBR } from '@/utils/date'
import { LABELS, labelTipoConta } from '@/utils/strings'
import ConfirmModal from '@/components/ConfirmModal.vue'

const router = useRouter()

// State
const loading = ref(true)
const contas = ref<Conta[]>([])
const contaADeletar = ref<Conta | null>(null)
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
  tipo: 'todas' as 'todas' | 'carteira' | 'conta_corrente' | 'poupanca' | 'cartao_credito' | 'investimento' | 'outro',
  busca: '',
  status: 'todas' as 'todas' | 'ativas' | 'inativas'
})

// Computed - Contas Filtradas
const contasFiltradas = computed(() => {
  let resultado = [...contas.value]
  
  // Filtro por tipo
  if (filtros.value.tipo !== 'todas') {
    resultado = resultado.filter(c => c.tipo === filtros.value.tipo)
  }
  
  // Filtro por status
  if (filtros.value.status === 'ativas') {
    resultado = resultado.filter(c => c.ativa)
  } else if (filtros.value.status === 'inativas') {
    resultado = resultado.filter(c => !c.ativa)
  }
  
  // Busca textual
  if (filtros.value.busca) {
    const busca = filtros.value.busca.toLowerCase()
    resultado = resultado.filter(c =>
      c.nome.toLowerCase().includes(busca)
    )
  }
  
  return resultado
})

// Computed - Totais
const totais = computed(() => {
  const saldoAtivas = contasFiltradas.value
    .filter(c => c.ativa)
    .reduce((sum, c) => sum + c.saldo, 0)
  
  const saldoInativas = contasFiltradas.value
    .filter(c => !c.ativa)
    .reduce((sum, c) => sum + c.saldo, 0)
  
  return {
    ativas: contasFiltradas.value.filter(c => c.ativa).length,
    inativas: contasFiltradas.value.filter(c => !c.ativa).length,
    saldoAtivas,
    saldoInativas,
    saldoTotal: saldoAtivas + saldoInativas
  }
})

// Metodos
const fetchDados = async () => {
  loading.value = true
  try {
    const contasRes = await api.get('/contas')
    contas.value = contasRes.data
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    loading.value = false
  }
}

const novaConta = () => {
  router.push('/contas/nova')
}

const editarConta = (id: number) => {
  router.push(`/contas/${id}/editar`)
}

const abrirFatura = (id: number) => {
  router.push(`/contas/${id}/fatura`)
}

const abrirModalDelete = (conta: Conta) => {
  contaADeletar.value = conta
  mostraModalDelete.value = true
}

const fecharModalDelete = () => {
  mostraModalDelete.value = false
  contaADeletar.value = null
}

const deletarConta = async () => {
  if (!contaADeletar.value) return
  
  const id = contaADeletar.value.id
  
  try {
    await api.delete(`/contas/${id}`)
    contas.value = contas.value.filter(c => c.id !== id)
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


const formatarData = (valor?: string | null): string => {
  if (!valor) return '-'
  return formatDateBR(valor)
}

const limparFiltros = () => {
  filtros.value = {
    tipo: 'todas',
    busca: '',
    status: 'todas'
  }
}

onMounted(() => {
  fetchDados()
})
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <!-- Header -->
    <div class="bg-base-100 shadow">
      <div class="container mx-auto px-4 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-2xl font-bold">Minhas Contas</h1>
          <button @click="novaConta" class="btn btn-primary">
            Nova Conta
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">Carregando contas...</p>
    </div>

    <!-- Content -->
    <div v-else class="container mx-auto px-4 py-8">
      
      <!-- Filtros -->
      <div class="card bg-base-100 shadow-md mb-6">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h3 class="card-title">Filtros</h3>
            <button @click="limparFiltros" class="btn btn-ghost btn-sm">
              Limpar Filtros
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Busca -->
            <div>
              <input
                v-model="filtros.busca"
                type="text"
                placeholder="Buscar por nome..."
                class="input input-bordered w-full"
              />
            </div>

            <!-- Tipo -->
            <div>
              <select v-model="filtros.tipo" class="select select-bordered w-full">
                <option value="todas">Todos os tipos</option>
                <option value="carteira">{{ LABELS.conta_carteira }}</option>
                <option value="conta_corrente">{{ LABELS.conta_corrente }}</option>
                <option value="poupanca">{{ LABELS.conta_poupanca }}</option>
                <option value="cartao_credito">{{ LABELS.conta_cartao }}</option>
                <option value="investimento">{{ LABELS.conta_investimento }}</option>
                <option value="outro">{{ LABELS.conta_outro }}</option>
              </select>
            </div>

            <!-- Status -->
            <div>
              <select v-model="filtros.status" class="select select-bordered w-full">
                <option value="todas">Todas</option>
                <option value="ativas">Ativas</option>
                <option value="inativas">Inativas</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumo -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div class="card bg-base-100 shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Saldo Total</p>
            <p class="text-2xl font-bold text-success tabular-nums">{{ formatarMoeda(totais.saldoTotal) }}</p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Contas Ativas</p>
            <p class="text-2xl font-bold text-info">{{ totais.ativas }}</p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Saldo Ativas</p>
            <p class="text-2xl font-bold tabular-nums">{{ formatarMoeda(totais.saldoAtivas) }}</p>
          </div>
        </div>

        <div class="card bg-base-100 shadow-md">
          <div class="card-body">
            <p class="text-sm text-gray-500">Inativas</p>
            <p class="text-2xl font-bold text-warning">{{ totais.inativas }}</p>
          </div>
        </div>
      </div>

      <!-- Lista de Contas -->
      <div v-if="contasFiltradas.length === 0" class="card bg-base-100 shadow-md">
        <div class="card-body text-center py-16">
          <p class="text-xl font-semibold mb-2">Nenhuma conta encontrada</p>
          <p class="text-gray-500 mb-6">
            {{ filtros.tipo !== 'todas' || filtros.busca || filtros.status !== 'todas'
              ? 'Tente ajustar os filtros'
              : 'Adicione sua primeira conta' }}
          </p>
          <button @click="novaConta" class="btn btn-primary">
            Nova Conta
          </button>
        </div>
      </div>

      <!-- Cards de Contas -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="conta in contasFiltradas"
          :key="conta.id"
          class="card bg-base-100 shadow-md hover:shadow-lg transition-shadow"
          :style="{ borderLeft: `5px solid ${conta.cor}` }"
        >
          <div class="card-body">
            <!-- Header -->
            <div class="flex justify-between items-start mb-4">
              <div class="flex-1">
                <h3 class="card-title text-lg">{{ conta.nome }}</h3>
                <p class="text-sm text-gray-500 mt-1">{{ labelTipoConta(conta.tipo) }}</p>
                <p v-if="conta.tipo === 'cartao_credito'" class="text-xs text-gray-500">
                  Fecha dia {{ conta.dia_fechamento ?? '-' }} | Vence dia {{ conta.dia_vencimento ?? '-' }}
                </p>
              </div>

              <!-- Status Badge -->
              <div v-if="conta.ativa" class="badge badge-success">Ativa</div>
              <div v-else class="badge badge-ghost">Inativa</div>
            </div>

            <!-- Saldo -->
            <div class="mb-4 p-4 rounded-lg bg-gray-50">
              <p class="text-sm text-gray-500 mb-1">Saldo</p>
              <p :class="[
                'text-3xl font-bold',
                conta.saldo >= 0 ? 'text-success' : 'text-error'
              ]">
                {{ formatarMoeda(conta.saldo) }}
              </p>
              <p
                v-if="conta.tipo === 'cartao_credito'"
                :class="[
                  'text-sm mt-2',
                  (conta.valor_fatura_fechada || 0) > 0 ? 'text-error' : 'text-success'
                ]"
              >
                Fatura a pagar: {{ formatarMoeda(conta.valor_fatura_fechada || 0) }}
              </p>
              <p v-if="conta.tipo === 'cartao_credito'" class="text-xs text-gray-500 mt-1">
                Pago na fatura fechada: {{ formatarMoeda(conta.valor_fatura_fechada_pago || 0) }}
              </p>
              <p v-if="conta.tipo === 'cartao_credito'" class="text-xs text-gray-500 mt-1">
                Fatura atual: {{ formatarMoeda(conta.valor_fatura_aberta || 0) }}
              </p>
              <p v-if="conta.tipo === 'cartao_credito' && conta.data_vencimento_fatura_fechada" class="text-xs text-gray-500 mt-1">
                Vencimento da fatura fechada: {{ formatarData(conta.data_vencimento_fatura_fechada) }}
              </p>
            </div>

            <!-- Informacoes -->
            <div class="divider my-2"></div>

            <!-- Acoes -->
            <div class="card-actions justify-end">
              <button
                v-if="conta.tipo === 'cartao_credito'"
                @click="abrirFatura(conta.id)"
                class="btn btn-sm btn-ghost"
              >
                Fatura
              </button>
              <button
                @click="editarConta(conta.id)"
                class="btn btn-sm btn-ghost"
              >
                Editar
              </button>
              <button
                @click="abrirModalDelete(conta)"
                class="btn btn-sm btn-ghost text-error"
              >
                Deletar
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Contador -->
      <div class="text-center mt-8 text-gray-500">
        {{ contasFiltradas.length }} conta(s) encontrada(s)
      </div>
    </div>

    <ConfirmModal
      v-model:open="mostraModalDelete"
      severity="cascade"
      :title="`Excluir a conta '${contaADeletar?.nome ?? ''}'?`"
      description="Esta ação vai apagar a conta e tudo que está ligado a ela. Não é possível desfazer."
      :impacts="[
        `Saldo de ${formatarMoeda(contaADeletar?.saldo ?? 0)} será descartado`,
        'Todas as transações da conta serão excluídas',
        'Transferências vinculadas perderão a referência',
      ]"
      confirm-label="Excluir conta"
      cancel-label="Manter conta"
      @confirm="deletarConta"
    />
    <!-- Modal de Erro -->
    <div v-if="showErrorModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">Erro</h3>
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
