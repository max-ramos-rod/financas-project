<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import type { FaturaResumo } from '@/types'
import { useContasStore } from '@/stores/contas'
import { formatDateBR, formatDateForInput } from '@/utils/date'
import { formatarMoeda } from '@/utils/financeiro'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import { Pencil, Trash2, X } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const contaId = Number(route.params.id)
const contasStore = useContasStore()
const { contas } = storeToRefs(contasStore)

const loading = ref(true)
const carregandoFatura = ref(false)
const pagando = ref(false)
const salvandoCiclo = ref(false)
const error = ref('')
const success = ref('')
const faturaAtualReferencia = ref<FaturaResumo | null>(null)
const faturaSelecionada = ref<FaturaResumo | null>(null)
const cicloSelecionado = ref('')
const contaPagamentoId = ref<number | null>(null)
const dataPagamento = ref(formatDateForInput(new Date()))
const dataFechamentoReal = ref('')
const dataVencimentoReal = ref('')
const observacaoCiclo = ref('')

type Aba = 'ajuste' | 'pagamento'
const abaAtiva = ref<Aba>('ajuste')

// Modal de exclusão unitária
const modalExcluirAberta = ref(false)
const transacaoParaExcluir = ref<{ id: number; descricao: string; valor: number } | null>(null)
const excluindo = ref(false)

// Seleção múltipla
const selectedIds = ref<Set<number>>(new Set())

const isSelected = (id: number) => selectedIds.value.has(id)

const toggleSelect = (id: number) => {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

const selectAll = () => {
  if (!faturaSelecionada.value) return
  selectedIds.value = new Set(faturaSelecionada.value.itens.map((i) => i.transacao_id))
}

const clearSelection = () => {
  selectedIds.value = new Set()
}

const allSelected = computed(() => {
  if (!faturaSelecionada.value || faturaSelecionada.value.itens.length === 0) return false
  return faturaSelecionada.value.itens.every((i) => selectedIds.value.has(i.transacao_id))
})

const someSelected = computed(() => selectedIds.value.size > 0)

// Bulk delete
const bulkParaDeletar = ref<number[]>([])
const showBulkDeleteModal = ref(false)

const iniciarBulkExcluir = () => {
  bulkParaDeletar.value = [...selectedIds.value]
  showBulkDeleteModal.value = true
}

const confirmarBulkExcluir = async () => {
  if (!bulkParaDeletar.value.length) return
  try {
    await api.delete('/transacoes/bulk', { data: { ids: bulkParaDeletar.value } })
    clearSelection()
    await carregarFaturaSelecionada(true)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao excluir transações.'
  }
}

const contasPagamento = computed(() =>
  contas.value.filter((c) => c.ativa && c.tipo !== 'cartao_credito' && c.id !== contaId)
)

const formatarData = (data: string): string => formatDateBR(data)

const chaveCiclo = (ano: number, mes: number): string => `${ano}-${String(mes).padStart(2, '0')}`

const parseCiclo = (chave: string): { ano: number; mes: number } => {
  const [ano, mes] = chave.split('-').map(Number)
  return { ano, mes }
}

const deslocarMes = (ano: number, mes: number, deslocamento: number): { ano: number; mes: number } => {
  const data = new Date(ano, mes - 1 + deslocamento, 1)
  return { ano: data.getFullYear(), mes: data.getMonth() + 1 }
}

const formatarMesAno = (ano: number, mes: number): string =>
  new Intl.DateTimeFormat('pt-BR', { month: 'short', year: 'numeric', timeZone: 'UTC' })
    .format(new Date(Date.UTC(ano, mes - 1, 1)))
    .replace('.', '')

const opcoesCiclo = computed(() => {
  if (!faturaAtualReferencia.value) return []
  const baseAno = faturaAtualReferencia.value.competencia_ano
  const baseMes = faturaAtualReferencia.value.competencia_mes

  return Array.from({ length: 16 }, (_, index) => {
    const deslocamento = index - 12
    const { ano, mes } = deslocarMes(baseAno, baseMes, deslocamento)
    return {
      chave: chaveCiclo(ano, mes),
      label: `${formatarMesAno(ano, mes)}${deslocamento === 0 ? ' (atual)' : ''}`,
    }
  }).reverse()
})


const novaTransacao = () => {
  router.push({
    path: '/transacoes/nova',
    query: {
      conta_id: contaId,
      ano: faturaSelecionada.value?.competencia_ano,
      mes: faturaSelecionada.value?.competencia_mes,
      tipo: 'saida',
      periodo_inicio: faturaSelecionada.value?.periodo_inicio,
      periodo_fim: faturaSelecionada.value?.periodo_fim,
    },
  })
}

const editarTransacao = (id: number) => {
  router.push({
    path: `/transacoes/${id}/editar`,
    query: {
      conta_id: contaId,
      ano: faturaSelecionada.value?.competencia_ano,
      mes: faturaSelecionada.value?.competencia_mes,
      periodo_inicio: faturaSelecionada.value?.periodo_inicio,
      periodo_fim: faturaSelecionada.value?.periodo_fim,
    },
  })
}

const abrirModalExcluir = (id: number, descricao: string, valor: number) => {
  transacaoParaExcluir.value = { id, descricao, valor }
  modalExcluirAberta.value = true
}

const confirmarExclusao = async () => {
  if (!transacaoParaExcluir.value) return
  excluindo.value = true
  try {
    await api.delete(`/transacoes/${transacaoParaExcluir.value.id}`)
    await carregarFaturaSelecionada(true)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao excluir transação.'
  } finally {
    excluindo.value = false
  }
}

const aplicarFaturaNaTela = (resumo: FaturaResumo) => {
  faturaSelecionada.value = resumo
  dataFechamentoReal.value = resumo.data_fechamento_real || ''
  dataVencimentoReal.value = resumo.data_vencimento_real || ''
  observacaoCiclo.value = resumo.observacao_ciclo || ''
}

const carregarFaturaSelecionada = async (manterMensagem = false) => {
  if (!cicloSelecionado.value) return
  if (!manterMensagem) {
    error.value = ''
    success.value = ''
  }
  clearSelection()
  carregandoFatura.value = true
  try {
    const { ano, mes } = parseCiclo(cicloSelecionado.value)
    const res = await api.get<FaturaResumo>(`/contas/${contaId}/faturas/${ano}/${mes}`)
    aplicarFaturaNaTela(res.data)
    router.replace({ query: { ...route.query, ano: String(ano), mes: String(mes) } })
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao carregar a fatura selecionada.'
  } finally {
    carregandoFatura.value = false
  }
}

const carregar = async () => {
  loading.value = true
  error.value = ''
  try {
    const [faturaAtualRes] = await Promise.all([
      api.get<FaturaResumo>(`/contas/${contaId}/fatura-atual`),
      contasStore.fetchContas(),
    ])

    faturaAtualReferencia.value = faturaAtualRes.data

    const anoQuery = Number(route.query.ano)
    const mesQuery = Number(route.query.mes)
    cicloSelecionado.value = anoQuery && mesQuery >= 1 && mesQuery <= 12
      ? chaveCiclo(anoQuery, mesQuery)
      : chaveCiclo(faturaAtualRes.data.competencia_ano, faturaAtualRes.data.competencia_mes)

    if (!contaPagamentoId.value && contasPagamento.value.length > 0) {
      contaPagamentoId.value = contasPagamento.value[0].id
    }

    await carregarFaturaSelecionada(true)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao carregar dados da fatura.'
  } finally {
    loading.value = false
  }
}

const salvarAjusteCiclo = async () => {
  if (!cicloSelecionado.value) return
  salvandoCiclo.value = true
  error.value = ''
  success.value = ''
  try {
    const { ano, mes } = parseCiclo(cicloSelecionado.value)
    const res = await api.put<FaturaResumo>(`/contas/${contaId}/faturas/${ano}/${mes}/ajuste-ciclo`, {
      data_fechamento_real: dataFechamentoReal.value || null,
      data_vencimento_real: dataVencimentoReal.value || null,
      observacao: observacaoCiclo.value || null,
    })
    aplicarFaturaNaTela(res.data)
    success.value = 'Ajuste do ciclo salvo com sucesso.'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao salvar ajuste do ciclo.'
  } finally {
    salvandoCiclo.value = false
  }
}

const limparAjusteCiclo = async () => {
  if (!cicloSelecionado.value) return
  salvandoCiclo.value = true
  error.value = ''
  success.value = ''
  try {
    const { ano, mes } = parseCiclo(cicloSelecionado.value)
    const res = await api.delete<FaturaResumo>(`/contas/${contaId}/faturas/${ano}/${mes}/ajuste-ciclo`)
    aplicarFaturaNaTela(res.data)
    success.value = 'Ajuste do ciclo removido.'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao limpar ajuste do ciclo.'
  } finally {
    salvandoCiclo.value = false
  }
}

const pagarFatura = async () => {
  if (!contaPagamentoId.value) {
    error.value = 'Selecione a conta de pagamento.'
    return
  }
  if (!cicloSelecionado.value) return

  pagando.value = true
  error.value = ''
  success.value = ''
  try {
    const { ano, mes } = parseCiclo(cicloSelecionado.value)
    const res = await api.post<FaturaResumo>(`/contas/${contaId}/faturas/${ano}/${mes}/pagar`, {
      conta_pagamento_id: contaPagamentoId.value,
      data_pagamento: dataPagamento.value,
    })
    aplicarFaturaNaTela(res.data)
    success.value = 'Fatura quitada com sucesso.'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao pagar fatura.'
  } finally {
    pagando.value = false
  }
}

const exportandoPdf = ref(false)
const exportarPdf = async () => {
  if (!faturaSelecionada.value) return
  exportandoPdf.value = true
  try {
    const { competencia_ano: ano, competencia_mes: mes } = faturaSelecionada.value
    const res = await api.get(`/contas/${contaId}/faturas/${ano}/${mes}/pdf`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data as BlobPart], { type: 'application/pdf' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `fatura_${contaId}_${ano}_${String(mes).padStart(2, '0')}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao gerar PDF.'
  } finally {
    exportandoPdf.value = false
  }
}

const exportandoCsv = ref(false)
const exportarCsv = async () => {
  if (!faturaSelecionada.value) return
  exportandoCsv.value = true
  try {
    const { competencia_ano: ano, competencia_mes: mes } = faturaSelecionada.value
    const res = await api.get(`/contas/${contaId}/faturas/${ano}/${mes}/csv`, { responseType: 'blob' })
    const url = URL.createObjectURL(new Blob([res.data as BlobPart], { type: 'text/csv' }))
    const a = document.createElement('a')
    a.href = url
    a.download = `fatura_${contaId}_${ano}_${String(mes).padStart(2, '0')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao gerar CSV.'
  } finally {
    exportandoCsv.value = false
  }
}

onMounted(carregar)
</script>

<template>
  <div class="min-h-screen bg-base-200">

    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">

      <!-- 1. Page header -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-5 lg:mb-6">
        <div>
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight">
            Fatura do Cartão
          </h1>
          <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-1">
            <template v-if="faturaSelecionada">
              {{ formatarMesAno(faturaSelecionada.competencia_ano, faturaSelecionada.competencia_mes) }}
              · {{ faturaSelecionada.total_itens }} {{ faturaSelecionada.total_itens === 1 ? 'lançamento' : 'lançamentos' }}
            </template>
            <template v-else>concilie, ajuste datas e pague faturas</template>
          </p>
        </div>
        <div class="flex gap-2">
          <button class="btn btn-ghost btn-sm sm:btn-md" @click="router.push('/contas')">
            ← Contas
          </button>
          <button
            class="btn btn-ghost btn-sm sm:btn-md whitespace-nowrap"
            :disabled="!faturaSelecionada || exportandoCsv"
            @click="exportarCsv"
          >
            <span v-if="exportandoCsv" class="loading loading-spinner loading-xs"></span>
            <span v-else>↓ CSV</span>
          </button>
          <button
            class="btn btn-ghost btn-sm sm:btn-md whitespace-nowrap"
            :disabled="!faturaSelecionada || exportandoPdf"
            @click="exportarPdf"
          >
            <span v-if="exportandoPdf" class="loading loading-spinner loading-xs"></span>
            <span v-else>↓ PDF</span>
          </button>
          <button
            class="btn btn-primary btn-sm sm:btn-md whitespace-nowrap"
            :disabled="!faturaSelecionada"
            @click="novaTransacao"
          >
            + Nova transação
          </button>
        </div>
      </div>

      <!-- Alertas -->
      <div v-if="error" class="alert alert-error mb-4"><span>{{ error }}</span></div>
      <div v-if="success" class="alert alert-success mb-4"><span>{{ success }}</span></div>

      <!-- 2. Toolbar: seletor de ciclo -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-3 sm:p-4 gap-0">
          <div class="flex flex-wrap items-end gap-2">
            <div class="flex-1 min-w-[200px]">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Ciclo da fatura</span>
              </label>
              <select
                v-model="cicloSelecionado"
                class="select select-bordered select-sm w-full"
                @change="carregarFaturaSelecionada()"
              >
                <option v-for="opcao in opcoesCiclo" :key="opcao.chave" :value="opcao.chave">
                  {{ opcao.label }}
                </option>
              </select>
            </div>
            <button
              class="btn btn-ghost btn-sm"
              :disabled="carregandoFatura"
              @click="carregarFaturaSelecionada()"
            >
              <span v-if="carregandoFatura" class="loading loading-spinner loading-xs"></span>
              <span v-else>↺</span>
            </button>
          </div>
        </div>
      </div>

      <template v-if="faturaSelecionada">

        <!-- 3. KPI strip -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-4">

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body py-4 px-4 gap-1">
              <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Total da fatura</p>
              <p class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap">
                {{ formatarMoeda(faturaSelecionada.valor_total) }}
              </p>
              <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
                {{ faturaSelecionada.total_itens }} lançamento(s)
              </p>
            </div>
          </div>

          <div class="card shadow-sm" :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'bg-error/10' : 'bg-base-100'">
            <div class="card-body py-4 px-4 gap-1">
              <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">A pagar</p>
              <p
                class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap"
                :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'text-error' : 'text-success'"
              >
                {{ formatarMoeda(faturaSelecionada.valor_a_pagar || 0) }}
              </p>
              <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
                {{ (faturaSelecionada.valor_a_pagar || 0) > 0 ? 'em aberto' : 'quitada' }}
              </p>
            </div>
          </div>

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body py-4 px-4 gap-1">
              <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Pago</p>
              <p class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap text-success">
                {{ formatarMoeda(faturaSelecionada.valor_pago || 0) }}
              </p>
              <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">liquidado</p>
            </div>
          </div>

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body py-4 px-4 gap-1">
              <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/50">Vencimento</p>
              <p class="text-lg sm:text-xl lg:text-2xl font-bold tabular-nums whitespace-nowrap">
                {{ formatarData(faturaSelecionada.data_vencimento_fatura) }}
              </p>
              <p class="text-[10px] font-mono text-base-content/40 mt-0.5 hidden sm:block">
                Fechamento: {{ formatarData(faturaSelecionada.data_fechamento_fatura) }}
              </p>
            </div>
          </div>

        </div>

        <!-- 4. Abas: Ajuste do Ciclo / Pagamento -->
        <div class="card bg-base-100 shadow-sm mb-4">
          <div class="border-b border-base-200">
            <div role="tablist" class="tabs tabs-bordered px-4 sm:px-6">
              <button
                role="tab"
                class="tab text-sm"
                :class="abaAtiva === 'ajuste' ? 'tab-active font-semibold' : ''"
                @click="abaAtiva = 'ajuste'"
              >
                Ajuste do Ciclo
              </button>
              <button
                role="tab"
                class="tab gap-2 text-sm"
                :class="abaAtiva === 'pagamento' ? 'tab-active font-semibold' : ''"
                @click="abaAtiva = 'pagamento'"
              >
                Pagamento
                <span v-if="(faturaSelecionada.valor_a_pagar || 0) > 0" class="badge badge-xs badge-error">!</span>
              </button>
            </div>
          </div>

          <!-- Aba: Ajuste do Ciclo -->
          <div v-if="abaAtiva === 'ajuste'" class="card-body p-4 sm:p-6 space-y-4">
            <p class="text-xs text-base-content/50">
              Registre exceções do mês: feriados, fins de semana ou mudanças operacionais do emissor.
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="form-control">
                <label class="label py-0 pb-1">
                  <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Fechamento previsto</span>
                </label>
                <input :value="faturaSelecionada.data_fechamento_prevista" type="date" class="input input-bordered input-sm w-full" disabled />
              </div>
              <div class="form-control">
                <label class="label py-0 pb-1">
                  <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Vencimento previsto</span>
                </label>
                <input :value="faturaSelecionada.data_vencimento_prevista" type="date" class="input input-bordered input-sm w-full" disabled />
              </div>
              <div class="form-control">
                <label class="label py-0 pb-1">
                  <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Fechamento real</span>
                </label>
                <input v-model="dataFechamentoReal" type="date" class="input input-bordered input-sm w-full" />
              </div>
              <div class="form-control">
                <label class="label py-0 pb-1">
                  <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Vencimento real</span>
                </label>
                <input v-model="dataVencimentoReal" type="date" class="input input-bordered input-sm w-full" />
              </div>
            </div>
            <div class="form-control">
              <label class="label py-0 pb-1">
                <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Observação</span>
              </label>
              <textarea
                v-model="observacaoCiclo"
                class="textarea textarea-bordered textarea-sm w-full"
                rows="2"
                placeholder="Ex.: banco postergou vencimento por feriado nacional."
              ></textarea>
            </div>
            <div class="flex gap-2 justify-end">
              <button class="btn btn-ghost btn-sm" :disabled="salvandoCiclo" @click="limparAjusteCiclo">
                Limpar
              </button>
              <button class="btn btn-secondary btn-sm" :disabled="salvandoCiclo" @click="salvarAjusteCiclo">
                <span v-if="salvandoCiclo" class="loading loading-spinner loading-xs"></span>
                <span v-else>Salvar ajuste</span>
              </button>
            </div>
          </div>

          <!-- Aba: Pagamento -->
          <div v-if="abaAtiva === 'pagamento'" class="card-body p-4 sm:p-6 space-y-4">
            <p class="text-xs text-base-content/50">
              {{ (faturaSelecionada.valor_a_pagar || 0) > 0
                ? `Valor em aberto: ${formatarMoeda(faturaSelecionada.valor_a_pagar || 0)}`
                : 'Esta fatura já está quitada.' }}
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="form-control">
                <label class="label py-0 pb-1">
                  <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Conta de pagamento</span>
                </label>
                <select v-model.number="contaPagamentoId" class="select select-bordered select-sm w-full">
                  <option :value="null">Selecione</option>
                  <option v-for="conta in contasPagamento" :key="conta.id" :value="conta.id">
                    {{ conta.nome }} ({{ formatarMoeda(conta.saldo) }})
                  </option>
                </select>
              </div>
              <div class="form-control">
                <label class="label py-0 pb-1">
                  <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Data de pagamento</span>
                </label>
                <input v-model="dataPagamento" type="date" class="input input-bordered input-sm w-full" />
              </div>
            </div>
            <div class="flex justify-end">
              <button
                class="btn btn-primary btn-sm sm:btn-md"
                :disabled="pagando || (faturaSelecionada.valor_a_pagar || 0) === 0"
                @click="pagarFatura"
              >
                <span v-if="pagando" class="loading loading-spinner loading-xs"></span>
                <span v-else>Confirmar pagamento</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 5. Lista de lançamentos -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body p-4 sm:p-6">

            <div class="flex items-center justify-between mb-4 lg:mb-5">
              <div>
                <h2 class="font-semibold text-base">Lançamentos do Ciclo</h2>
                <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-0.5">
                  {{ faturaSelecionada.itens.length === 0
                    ? 'nenhum lançamento'
                    : `${faturaSelecionada.itens.length} lançamento(s)` }}
                  · {{ formatarData(faturaSelecionada.periodo_inicio) }} – {{ formatarData(faturaSelecionada.periodo_fim) }}
                </p>
              </div>
            </div>

            <div v-if="faturaSelecionada.itens.length === 0" class="py-12 text-center text-base-content/30 text-sm">
              Nenhum lançamento neste ciclo.
            </div>

            <template v-else>

              <!-- Desktop: tabela -->
              <div class="hidden md:block overflow-x-auto">
                <table class="table table-sm w-full">
                  <thead>
                    <tr class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 border-b border-base-200">
                      <th class="w-8 pl-0">
                        <input
                          type="checkbox"
                          class="checkbox checkbox-xs"
                          :checked="allSelected"
                          :indeterminate="someSelected && !allSelected"
                          @change="allSelected ? clearSelection() : selectAll()"
                        />
                      </th>
                      <th class="font-medium">Descrição</th>
                      <th class="font-medium">Data</th>
                      <th class="font-medium">Vencimento</th>
                      <th class="font-medium">Status</th>
                      <th class="font-medium text-right pr-0">Valor</th>
                      <th class="w-16"></th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-base-200">
                    <tr
                      v-for="item in faturaSelecionada.itens"
                      :key="item.transacao_id"
                      class="transition-colors"
                      :class="isSelected(item.transacao_id) ? 'bg-base-200/30' : 'hover:bg-base-50'"
                    >
                      <td class="pl-0 w-8">
                        <input
                          type="checkbox"
                          class="checkbox checkbox-xs"
                          :checked="isSelected(item.transacao_id)"
                          @change="toggleSelect(item.transacao_id)"
                        />
                      </td>
                      <td class="font-medium text-sm max-w-[220px] truncate">
                        {{ item.descricao }}
                        <span v-if="item.tipo === 'entrada'" class="ml-1.5 badge badge-xs badge-success">crédito</span>
                      </td>
                      <td class="text-sm text-base-content/60 whitespace-nowrap">{{ formatarData(item.data) }}</td>
                      <td class="text-sm text-base-content/60 whitespace-nowrap">
                        {{ item.data_vencimento ? formatarData(item.data_vencimento) : '—' }}
                      </td>
                      <td>
                        <span
                          class="badge badge-sm whitespace-nowrap"
                          :class="item.status_liquidacao === 'liquidado' ? 'badge-success' : 'badge-warning'"
                        >{{ item.status_liquidacao }}</span>
                      </td>
                      <td
                        class="text-right pr-0 font-bold text-sm whitespace-nowrap tabular-nums"
                        :class="item.tipo === 'entrada' ? 'text-success' : (item.status_liquidacao === 'liquidado' ? 'text-success' : 'text-error')"
                      >
                        {{ item.tipo === 'entrada' ? '− ' : '' }}{{ formatarMoeda(item.valor_efetivo) }}
                      </td>
                      <td class="pr-0">
                        <div class="flex items-center gap-1 justify-end">
                          <button
                            class="btn btn-ghost btn-xs opacity-30 hover:opacity-100"
                            @click="editarTransacao(item.transacao_id)"
                          ><Pencil :size="12" /></button>
                          <button
                            class="btn btn-ghost btn-xs text-error opacity-30 hover:opacity-100"
                            @click="abrirModalExcluir(item.transacao_id, item.descricao, item.valor_efetivo)"
                          >×</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- Mobile: lista -->
              <div class="md:hidden divide-y divide-base-200">
                <div
                  v-for="item in faturaSelecionada.itens"
                  :key="item.transacao_id"
                  class="py-3 flex items-start gap-3 transition-colors"
                  :class="isSelected(item.transacao_id) ? 'bg-base-200/30' : ''"
                >
                  <input
                    type="checkbox"
                    class="checkbox checkbox-xs mt-1 shrink-0"
                    :checked="isSelected(item.transacao_id)"
                    @change="toggleSelect(item.transacao_id)"
                  />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">
                      {{ item.descricao }}
                      <span v-if="item.tipo === 'entrada'" class="ml-1 badge badge-xs badge-success">crédito</span>
                    </p>
                    <p class="text-xs text-base-content/50 mt-0.5">
                      {{ formatarData(item.data) }}
                      <span v-if="item.data_vencimento"> · Venc. {{ formatarData(item.data_vencimento) }}</span>
                    </p>
                    <span
                      class="badge badge-sm whitespace-nowrap mt-1"
                      :class="item.status_liquidacao === 'liquidado' ? 'badge-success' : 'badge-warning'"
                    >{{ item.status_liquidacao }}</span>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <p
                      class="text-sm font-bold tabular-nums"
                      :class="item.tipo === 'entrada' ? 'text-success' : (item.status_liquidacao === 'liquidado' ? 'text-success' : 'text-error')"
                    >
                      {{ item.tipo === 'entrada' ? '− ' : '' }}{{ formatarMoeda(item.valor_efetivo) }}
                    </p>
                    <button
                      class="btn btn-ghost btn-xs opacity-30 hover:opacity-100"
                      @click="editarTransacao(item.transacao_id)"
                    ><Pencil :size="12" /></button>
                    <button
                      class="btn btn-ghost btn-xs text-error opacity-30 hover:opacity-100"
                      @click="abrirModalExcluir(item.transacao_id, item.descricao, item.valor_efetivo)"
                    >×</button>
                  </div>
                </div>
              </div>

              <!-- Rodapé total -->
              <div class="flex justify-between items-center pt-4 mt-2 border-t border-base-200">
                <span class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40">Total do ciclo</span>
                <span class="text-base font-bold tabular-nums">{{ formatarMoeda(faturaSelecionada.valor_total) }}</span>
              </div>

            </template>
          </div>
        </div>

      </template>
    </div>
  </div>

  <ConfirmModal
    v-model:open="modalExcluirAberta"
    severity="simple"
    title="Excluir transação?"
    description="Esta ação não pode ser desfeita."
    :impacts="transacaoParaExcluir
      ? [`${transacaoParaExcluir.descricao} — ${formatarMoeda(transacaoParaExcluir.valor)}`]
      : []"
    confirm-label="Excluir"
    cancel-label="Cancelar"
    @confirm="confirmarExclusao"
    @cancel="transacaoParaExcluir = null"
  />

  <ConfirmModal
    v-model:open="showBulkDeleteModal"
    severity="warn"
    :title="`Excluir ${bulkParaDeletar.length} lançamento${bulkParaDeletar.length === 1 ? '' : 's'}?`"
    description="Esta ação não pode ser desfeita."
    confirm-label="Excluir tudo"
    cancel-label="Cancelar"
    @confirm="confirmarBulkExcluir"
  />

  <!-- Barra de ações em massa -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-200"
      enter-from-class="opacity-0 translate-y-4"
      leave-active-class="transition-all duration-150"
      leave-to-class="opacity-0 translate-y-4"
    >
      <div
        v-if="someSelected"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-base-300 rounded-full shadow-xl px-4 py-2.5 border border-base-200 whitespace-nowrap"
      >
        <span class="text-sm font-medium px-1">
          {{ selectedIds.size }} {{ selectedIds.size === 1 ? 'selecionado' : 'selecionados' }}
        </span>
        <div class="w-px h-5 bg-base-content/20 shrink-0"></div>
        <button
          class="btn btn-ghost btn-sm gap-1.5 text-error"
          @click="iniciarBulkExcluir"
        >
          <Trash2 :size="15" />
          Excluir
        </button>
        <button class="btn btn-ghost btn-sm btn-circle" @click="clearSelection()">
          <X :size="15" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>
