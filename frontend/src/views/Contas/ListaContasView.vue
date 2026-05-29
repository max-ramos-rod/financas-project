<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import type { Conta } from '@/types'
import { extractApiError } from '@/services/apiError'
import { formatDateBR } from '@/utils/date'
import { LABELS, labelTipoConta } from '@/utils/strings'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Landmark } from '@lucide/vue'
import { useContasStore } from '@/stores/contas'

const router = useRouter()
const contasStore = useContasStore()
const { contas, loading } = storeToRefs(contasStore)
const contaADeletar = ref<Conta | null>(null)
const mostraModalDelete = ref(false)
const showErrorModal = ref(false)
const errorMessages = ref<string[]>([])


const filtros = ref({
  tipo: 'todas' as 'todas' | 'carteira' | 'conta_corrente' | 'poupanca' | 'cartao_credito' | 'investimento' | 'outro',
  busca: '',
  status: 'todas' as 'todas' | 'ativas' | 'inativas',
})

const contasFiltradas = computed(() => {
  let resultado = [...contas.value]
  if (filtros.value.tipo !== 'todas') resultado = resultado.filter(c => c.tipo === filtros.value.tipo)
  if (filtros.value.status === 'ativas') resultado = resultado.filter(c => c.ativa)
  else if (filtros.value.status === 'inativas') resultado = resultado.filter(c => !c.ativa)
  if (filtros.value.busca) {
    const busca = filtros.value.busca.toLowerCase()
    resultado = resultado.filter(c => c.nome.toLowerCase().includes(busca))
  }
  return resultado
})

const totais = computed(() => {
  const ativas = contasFiltradas.value.filter(c => c.ativa)
  const inativas = contasFiltradas.value.filter(c => !c.ativa)
  return {
    ativas: ativas.length,
    inativas: inativas.length,
    saldoAtivas: ativas.reduce((s, c) => s + c.saldo, 0),
    saldoInativas: inativas.reduce((s, c) => s + c.saldo, 0),
    saldoTotal: contasFiltradas.value.reduce((s, c) => s + c.saldo, 0),
  }
})

const temFiltrosAtivos = computed(() =>
  filtros.value.tipo !== 'todas' || filtros.value.busca !== '' || filtros.value.status !== 'todas'
)

const fetchDados = () => contasStore.fetchContas()

const novaConta = () => router.push('/contas/nova')
const editarConta = (id: number) => router.push(`/contas/${id}/editar`)
const abrirFatura = (id: number) => router.push(`/contas/${id}/fatura`)

const abrirModalDelete = (conta: Conta) => { contaADeletar.value = conta; mostraModalDelete.value = true }
const deletarConta = async () => {
  if (!contaADeletar.value) return
  const id = contaADeletar.value.id
  try {
    await contasStore.remover(id)
  } catch (error) {
    errorMessages.value = [extractApiError(error)]
    showErrorModal.value = true
  }
}

const limparFiltros = () => { filtros.value = { tipo: 'todas', busca: '', status: 'todas' } }

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarData = (valor?: string | null) => (!valor ? '-' : formatDateBR(valor))

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
            {{ LABELS.contas }}
          </h1>
          <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-1">
            {{ contasFiltradas.length }}
            {{ contasFiltradas.length === 1 ? 'conta' : 'contas' }}
            <template v-if="temFiltrosAtivos"> · filtradas</template>
          </p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-primary btn-sm sm:btn-md whitespace-nowrap" @click="novaConta">
            Nova Conta
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
                placeholder="Buscar por nome…"
              />
            </div>

            <!-- Segmented status -->
            <div class="join">
              <button
                class="join-item btn btn-sm"
                :class="filtros.status === 'todas' ? 'btn-primary' : 'btn-ghost border border-base-300'"
                @click="filtros.status = 'todas'"
              >Todas</button>
              <button
                class="join-item btn btn-sm"
                :class="filtros.status === 'ativas' ? 'btn-success' : 'btn-ghost border border-base-300'"
                @click="filtros.status = 'ativas'"
              >Ativas</button>
              <button
                class="join-item btn btn-sm"
                :class="filtros.status === 'inativas' ? 'btn-ghost btn-active' : 'btn-ghost border border-base-300'"
                @click="filtros.status = 'inativas'"
              >Inativas</button>
            </div>

            <!-- Tipo -->
            <select v-model="filtros.tipo" class="select select-bordered select-sm w-auto">
              <option value="todas">Todos os tipos</option>
              <option value="carteira">{{ LABELS.conta_carteira }}</option>
              <option value="conta_corrente">{{ LABELS.conta_corrente }}</option>
              <option value="poupanca">{{ LABELS.conta_poupanca }}</option>
              <option value="cartao_credito">{{ LABELS.conta_cartao }}</option>
              <option value="investimento">{{ LABELS.conta_investimento }}</option>
              <option value="outro">{{ LABELS.conta_outro }}</option>
            </select>

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
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Saldo Total</p>
            <p :class="['text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap', totais.saldoTotal >= 0 ? 'text-success' : 'text-error']">
              {{ formatarMoeda(totais.saldoTotal) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ totais.ativas }} ativas · {{ totais.inativas }} inativas
            </p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Contas Ativas</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-success tabular-nums">{{ totais.ativas }}</p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ formatarMoeda(totais.saldoAtivas) }}
            </p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Saldo Ativas</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap">
              {{ formatarMoeda(totais.saldoAtivas) }}
            </p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">em contas ativas</p>
          </div>
        </div>
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body py-4 px-4 gap-1">
            <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Inativas</p>
            <p class="text-lg sm:text-xl lg:text-2xl font-bold text-base-content/40 tabular-nums">{{ totais.inativas }}</p>
            <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
              {{ formatarMoeda(totais.saldoInativas) }}
            </p>
          </div>
        </div>
      </div>

      <!-- 4. Grid de contas -->
      <div v-if="contasFiltradas.length === 0" class="card bg-base-100 shadow-sm">
        <div class="card-body py-12">
          <EmptyState
            v-if="temFiltrosAtivos"
            variant="filtered"
            title="Nenhuma conta encontrada."
            description="Tente ajustar os filtros para ver mais resultados."
          >
            <template #icon><Landmark /></template>
            <template #actions>
              <button class="btn btn-ghost btn-sm" @click="limparFiltros">Limpar filtros</button>
            </template>
          </EmptyState>
          <EmptyState
            v-else
            variant="first-time"
            title="Nenhuma conta cadastrada."
            description="Adicione sua primeira conta para começar a controlar seu saldo."
          >
            <template #icon><Landmark /></template>
            <template #actions>
              <button class="btn btn-primary btn-sm" @click="novaConta">Nova Conta</button>
            </template>
          </EmptyState>
        </div>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="conta in contasFiltradas"
          :key="conta.id"
          class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow"
          :style="{ borderLeft: `4px solid ${conta.cor}` }"
        >
          <div class="card-body p-5 gap-3">

            <!-- Header -->
            <div class="flex items-start justify-between gap-2">
              <div class="min-w-0 flex-1">
                <h3 class="font-semibold text-base truncate">{{ conta.nome }}</h3>
                <p class="text-xs text-base-content/50 mt-0.5">{{ labelTipoConta(conta.tipo) }}</p>
                <p v-if="conta.tipo === 'cartao_credito'" class="text-xs text-base-content/40 mt-0.5">
                  Fecha dia {{ conta.dia_fechamento ?? '-' }} · Vence dia {{ conta.dia_vencimento ?? '-' }}
                </p>
              </div>
              <span v-if="conta.ativa" class="badge badge-success badge-sm shrink-0">Ativa</span>
              <span v-else class="badge badge-ghost badge-sm shrink-0">Inativa</span>
            </div>

            <!-- Saldo -->
            <div class="rounded-lg bg-base-200 px-4 py-3">
              <p class="text-[10px] font-mono uppercase tracking-widest text-base-content/40 mb-1">Saldo</p>
              <p :class="['text-2xl font-bold tabular-nums', conta.saldo >= 0 ? 'text-success' : 'text-error']">
                {{ formatarMoeda(conta.saldo) }}
              </p>

              <!-- Info cartão de crédito -->
              <template v-if="conta.tipo === 'cartao_credito'">
                <div class="mt-2 space-y-0.5">
                  <p :class="['text-xs tabular-nums', (conta.valor_fatura_fechada || 0) > 0 ? 'text-error' : 'text-base-content/50']">
                    Fatura a pagar: {{ formatarMoeda(conta.valor_fatura_fechada || 0) }}
                  </p>
                  <p class="text-xs text-base-content/40 tabular-nums">
                    Fatura atual: {{ formatarMoeda(conta.valor_fatura_aberta || 0) }}
                  </p>
                  <p v-if="conta.data_vencimento_fatura_fechada" class="text-xs text-base-content/40">
                    Vence em: {{ formatarData(conta.data_vencimento_fatura_fechada) }}
                  </p>
                </div>
              </template>
            </div>

            <!-- Ações -->
            <div class="flex gap-1 justify-end pt-1 border-t border-base-200">
              <button
                v-if="conta.tipo === 'cartao_credito'"
                class="btn btn-ghost btn-xs text-primary"
                @click="abrirFatura(conta.id)"
              >Fatura</button>
              <button class="btn btn-ghost btn-xs" @click="editarConta(conta.id)">Editar</button>
              <button class="btn btn-ghost btn-xs text-error" @click="abrirModalDelete(conta)">Deletar</button>
            </div>

          </div>
        </div>
      </div>

      <!-- Rodapé contador -->
      <div v-if="contasFiltradas.length > 0" class="text-center mt-6">
        <span class="font-mono text-[11px] text-base-content/40">
          {{ contasFiltradas.length }} {{ contasFiltradas.length === 1 ? 'conta' : 'contas' }} exibida(s)
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
