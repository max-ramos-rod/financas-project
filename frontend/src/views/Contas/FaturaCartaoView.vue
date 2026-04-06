<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import type { Conta, FaturaResumo } from '@/types'
import { formatDateBR, formatDateForInput } from '@/utils/date'

const route = useRoute()
const router = useRouter()
const contaId = Number(route.params.id)

const loading = ref(true)
const pagando = ref(false)
const salvandoCiclo = ref(false)
const error = ref('')
const success = ref('')
const faturaFechada = ref<FaturaResumo | null>(null)
const cicloAberto = ref<FaturaResumo | null>(null)
const contas = ref<Conta[]>([])
const contaPagamentoId = ref<number | null>(null)
const dataPagamento = ref(formatDateForInput(new Date()))
const dataFechamentoReal = ref('')
const dataVencimentoReal = ref('')
const observacaoCiclo = ref('')

const contasPagamento = computed(() =>
  contas.value.filter((c) => c.ativa && c.tipo !== 'cartao_credito' && c.id !== contaId)
)

const formatarMoeda = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarData = (data: string): string => formatDateBR(data)

const aplicarCicloAbertoNaTela = (resumo: FaturaResumo) => {
  cicloAberto.value = resumo
  dataFechamentoReal.value = resumo.data_fechamento_real || ''
  dataVencimentoReal.value = resumo.data_vencimento_fatura !== resumo.data_vencimento_prevista
    ? resumo.data_vencimento_fatura
    : ''
  observacaoCiclo.value = resumo.observacao_ciclo || ''
}

const carregar = async () => {
  loading.value = true
  error.value = ''
  try {
    const [faturaFechadaRes, cicloAbertoRes, contasRes] = await Promise.all([
      api.get<FaturaResumo>(`/contas/${contaId}/fatura-fechada`),
      api.get<FaturaResumo>(`/contas/${contaId}/fatura-atual`),
      api.get<Conta[]>('/contas'),
    ])
    faturaFechada.value = faturaFechadaRes.data
    aplicarCicloAbertoNaTela(cicloAbertoRes.data)
    contas.value = contasRes.data
    if (!contaPagamentoId.value && contasPagamento.value.length > 0) {
      contaPagamentoId.value = contasPagamento.value[0].id
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao carregar dados da fatura.'
  } finally {
    loading.value = false
  }
}

const salvarAjusteCiclo = async () => {
  salvandoCiclo.value = true
  error.value = ''
  success.value = ''
  try {
    const res = await api.put<FaturaResumo>(`/contas/${contaId}/fatura-atual/ajuste-ciclo`, {
      data_fechamento_real: dataFechamentoReal.value || null,
      data_vencimento_real: dataVencimentoReal.value || null,
      observacao: observacaoCiclo.value || null,
    })
    aplicarCicloAbertoNaTela(res.data)
    success.value = 'Ajuste do ciclo salvo com sucesso.'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao salvar ajuste do ciclo.'
  } finally {
    salvandoCiclo.value = false
  }
}

const limparAjusteCiclo = async () => {
  salvandoCiclo.value = true
  error.value = ''
  success.value = ''
  try {
    const res = await api.delete<FaturaResumo>(`/contas/${contaId}/fatura-atual/ajuste-ciclo`)
    aplicarCicloAbertoNaTela(res.data)
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
  pagando.value = true
  error.value = ''
  success.value = ''
  try {
    await api.post<FaturaResumo>(`/contas/${contaId}/pagar-fatura`, {
      conta_pagamento_id: contaPagamentoId.value,
      data_pagamento: dataPagamento.value,
    })
    await carregar()
    success.value = 'Fatura a pagar quitada com sucesso.'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao pagar fatura.'
  } finally {
    pagando.value = false
  }
}

onMounted(carregar)
</script>

<template>
  <div class="min-h-screen bg-base-200 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">Fatura do Cartao</h1>
        <button class="btn btn-ghost" @click="router.push('/contas')">Voltar</button>
      </div>

      <div v-if="loading" class="text-center py-10">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <template v-else>
        <div v-if="error" class="alert alert-error"><span>{{ error }}</span></div>
        <div v-if="success" class="alert alert-success"><span>{{ success }}</span></div>

        <div
          v-if="faturaFechada"
          class="card bg-base-100 shadow"
          :class="(faturaFechada.valor_a_pagar || 0) > 0 ? 'border border-error/20' : 'border border-success/20'"
        >
          <div class="card-body">
            <div>
              <h2 class="card-title">Ultima Fatura Fechada</h2>
              <p class="text-sm text-gray-500">Ultima fatura consolidada do cartao, paga ou ainda a vencer.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
              <div class="rounded-box bg-base-200 p-4">
                <p class="text-sm text-gray-500">Periodo fechado</p>
                <p class="font-semibold">{{ formatarData(faturaFechada.periodo_inicio) }} - {{ formatarData(faturaFechada.periodo_fim) }}</p>
                <p class="text-xs text-gray-500 mt-1">Fechamento: {{ formatarData(faturaFechada.data_fechamento_fatura) }}</p>
              </div>
              <div class="rounded-box bg-base-200 p-4">
                <p class="text-sm text-gray-500">Vencimento</p>
                <p class="font-semibold">{{ formatarData(faturaFechada.data_vencimento_fatura) }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ faturaFechada.total_itens }} item(ns)</p>
              </div>
              <div
                class="rounded-box p-4"
                :class="(faturaFechada.valor_a_pagar || 0) > 0 ? 'bg-error text-error-content' : 'bg-success text-success-content'"
              >
                <p class="text-sm opacity-80">Total da fatura fechada</p>
                <p class="text-3xl font-bold">{{ formatarMoeda(faturaFechada.valor_total) }}</p>
                <p class="text-xs opacity-80 mt-2">Pago: {{ formatarMoeda(faturaFechada.valor_pago || 0) }}</p>
                <p class="text-xs opacity-80">A pagar: {{ formatarMoeda(faturaFechada.valor_a_pagar || 0) }}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div>
                <label class="label"><span class="label-text">Conta de pagamento</span></label>
                <select v-model.number="contaPagamentoId" class="select select-bordered w-full">
                  <option :value="null">Selecione</option>
                  <option v-for="conta in contasPagamento" :key="conta.id" :value="conta.id">
                    {{ conta.nome }} ({{ formatarMoeda(conta.saldo) }})
                  </option>
                </select>
              </div>
              <div>
                <label class="label"><span class="label-text">Data de pagamento</span></label>
                <input v-model="dataPagamento" type="date" class="input input-bordered w-full" />
              </div>
              <div class="flex items-end">
                <button class="btn btn-primary w-full" :disabled="pagando || !faturaFechada || (faturaFechada.valor_a_pagar || 0) === 0" @click="pagarFatura">
                  <span v-if="pagando" class="loading loading-spinner loading-sm"></span>
                  <span v-else>Pagar</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="cicloAberto" class="card bg-base-100 shadow">
          <div class="card-body">
            <div>
              <h2 class="card-title">Fatura Atual</h2>
              <p class="text-sm text-gray-500">Lancamentos do ciclo em que estamos agora.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
              <div class="rounded-box bg-base-200 p-4">
                <p class="text-sm text-gray-500">Periodo do ciclo</p>
                <p class="font-semibold">{{ formatarData(cicloAberto.periodo_inicio) }} - {{ formatarData(cicloAberto.periodo_fim) }}</p>
                <p class="text-xs text-gray-500 mt-1">Fechamento do ciclo: {{ formatarData(cicloAberto.data_fechamento_fatura) }}</p>
              </div>
              <div class="rounded-box bg-base-200 p-4">
                <p class="text-sm text-gray-500">Vencimento previsto</p>
                <p class="font-semibold">{{ formatarData(cicloAberto.data_vencimento_fatura) }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ cicloAberto.total_itens }} item(ns)</p>
              </div>
              <div class="rounded-box bg-primary text-primary-content p-4">
                <p class="text-sm opacity-80">Parcial da fatura atual</p>
                <p class="text-3xl font-bold">{{ formatarMoeda(cicloAberto.valor_total) }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="cicloAberto" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Ajuste da Fatura Atual</h2>
            <p class="text-sm text-gray-500">
              Registre aqui excecoes do mes, como feriados, fins de semana ou mudancas operacionais do emissor.
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="label"><span class="label-text">Fechamento previsto</span></label>
                <input :value="cicloAberto.data_fechamento_prevista" type="date" class="input input-bordered w-full" disabled />
              </div>
              <div>
                <label class="label"><span class="label-text">Vencimento previsto</span></label>
                <input :value="cicloAberto.data_vencimento_prevista" type="date" class="input input-bordered w-full" disabled />
              </div>
              <div>
                <label class="label"><span class="label-text">Fechamento real do ciclo</span></label>
                <input v-model="dataFechamentoReal" type="date" class="input input-bordered w-full" />
              </div>
              <div>
                <label class="label"><span class="label-text">Vencimento real da fatura</span></label>
                <input v-model="dataVencimentoReal" type="date" class="input input-bordered w-full" />
              </div>
            </div>
            <div>
              <label class="label"><span class="label-text">Observacao do ciclo</span></label>
              <textarea
                v-model="observacaoCiclo"
                class="textarea textarea-bordered w-full"
                rows="3"
                placeholder="Ex.: banco postergou vencimento por feriado nacional."
              ></textarea>
            </div>
            <div class="flex flex-col md:flex-row gap-3 md:justify-end">
              <button class="btn btn-ghost" :disabled="salvandoCiclo" @click="limparAjusteCiclo">
                Limpar ajuste
              </button>
              <button class="btn btn-secondary" :disabled="salvandoCiclo" @click="salvarAjusteCiclo">
                <span v-if="salvandoCiclo" class="loading loading-spinner loading-sm"></span>
                <span v-else>Salvar ajuste do ciclo</span>
              </button>
            </div>
          </div>
        </div>

        <div v-if="cicloAberto" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Lancamentos da Fatura Atual</h2>
            <div v-if="cicloAberto.itens.length === 0" class="text-gray-500 py-6">Nenhum item em aberto no ciclo atual.</div>
            <div v-else class="space-y-2">
              <div v-for="item in cicloAberto.itens" :key="item.transacao_id" class="border rounded-lg p-3 flex items-center justify-between">
                <div>
                  <p class="font-medium">{{ item.descricao }}</p>
                  <p class="text-xs text-gray-500">
                    {{ formatarData(item.data) }}
                    <span v-if="item.data_vencimento"> | Venc: {{ formatarData(item.data_vencimento) }}</span>
                  </p>
                </div>
                <p class="font-bold text-error">{{ formatarMoeda(item.valor_efetivo) }}</p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
