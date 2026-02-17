<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import type { Conta, FaturaResumo } from '@/types'

const route = useRoute()
const router = useRouter()
const contaId = Number(route.params.id)

const loading = ref(true)
const pagando = ref(false)
const error = ref('')
const success = ref('')
const fatura = ref<FaturaResumo | null>(null)
const contas = ref<Conta[]>([])
const contaPagamentoId = ref<number | null>(null)
const dataPagamento = ref(new Date().toISOString().split('T')[0])

const contasPagamento = computed(() =>
  contas.value.filter((c) => c.ativa && c.tipo !== 'cartao_credito' && c.id !== contaId)
)

const formatarMoeda = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarData = (data: string): string =>
  new Date(data).toLocaleDateString('pt-BR')

const carregar = async () => {
  loading.value = true
  error.value = ''
  try {
    const [faturaRes, contasRes] = await Promise.all([
      api.get<FaturaResumo>(`/contas/${contaId}/fatura-atual`),
      api.get<Conta[]>('/contas'),
    ])
    fatura.value = faturaRes.data
    contas.value = contasRes.data
    if (!contaPagamentoId.value && contasPagamento.value.length > 0) {
      contaPagamentoId.value = contasPagamento.value[0].id
    }
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao carregar fatura.'
  } finally {
    loading.value = false
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
    const res = await api.post<FaturaResumo>(`/contas/${contaId}/pagar-fatura`, {
      conta_pagamento_id: contaPagamentoId.value,
      data_pagamento: dataPagamento.value,
    })
    fatura.value = res.data
    success.value = 'Fatura paga com sucesso.'
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
    <div class="max-w-5xl mx-auto space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">💳 Fatura do Cartao</h1>
        <button class="btn btn-ghost" @click="router.push('/contas')">Voltar</button>
      </div>

      <div v-if="loading" class="text-center py-10">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <template v-else>
        <div v-if="error" class="alert alert-error"><span>{{ error }}</span></div>
        <div v-if="success" class="alert alert-success"><span>{{ success }}</span></div>

        <div v-if="fatura" class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="card bg-base-100 shadow">
            <div class="card-body">
              <p class="text-sm text-gray-500">Cartao</p>
              <p class="font-semibold">{{ fatura.conta_nome }}</p>
              <p class="text-xs text-gray-500">Fechamento dia {{ fatura.dia_fechamento }}</p>
            </div>
          </div>
          <div class="card bg-base-100 shadow">
            <div class="card-body">
              <p class="text-sm text-gray-500">Periodo</p>
              <p class="font-semibold">{{ formatarData(fatura.periodo_inicio) }} - {{ formatarData(fatura.periodo_fim) }}</p>
              <p class="text-xs text-gray-500">Vencimento: {{ formatarData(fatura.data_vencimento_fatura) }}</p>
            </div>
          </div>
          <div class="card bg-primary text-primary-content shadow">
            <div class="card-body">
              <p class="text-sm opacity-90">Total em aberto</p>
              <p class="text-3xl font-bold">{{ formatarMoeda(fatura.valor_total) }}</p>
              <p class="text-xs opacity-80">{{ fatura.total_itens }} item(ns)</p>
            </div>
          </div>
        </div>

        <div v-if="fatura" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Pagar Fatura</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                <button class="btn btn-primary w-full" :disabled="pagando || !fatura || fatura.total_itens === 0" @click="pagarFatura">
                  <span v-if="pagando" class="loading loading-spinner loading-sm"></span>
                  <span v-else>Pagar {{ formatarMoeda(fatura?.valor_total || 0) }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="fatura" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Itens da Fatura</h2>
            <div v-if="fatura.itens.length === 0" class="text-gray-500 py-6">Nenhum item em aberto no ciclo atual.</div>
            <div v-else class="space-y-2">
              <div v-for="item in fatura.itens" :key="item.transacao_id" class="border rounded-lg p-3 flex items-center justify-between">
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
