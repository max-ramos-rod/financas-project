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
const carregandoFatura = ref(false)
const pagando = ref(false)
const salvandoCiclo = ref(false)
const error = ref('')
const success = ref('')
const faturaAtualReferencia = ref<FaturaResumo | null>(null)
const faturaSelecionada = ref<FaturaResumo | null>(null)
const contas = ref<Conta[]>([])
const cicloSelecionado = ref('')
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
      label: `${formatarMesAno(ano, mes)}${deslocamento === 0 ? ' (fatura atual)' : ''}`,
    }
  }).reverse()
})

const cicloAtualSelecionado = computed(() =>
  Boolean(faturaAtualReferencia.value && cicloSelecionado.value === chaveCiclo(
    faturaAtualReferencia.value.competencia_ano,
    faturaAtualReferencia.value.competencia_mes
  ))
)

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
    const [faturaAtualRes, contasRes] = await Promise.all([
      api.get<FaturaResumo>(`/contas/${contaId}/fatura-atual`),
      api.get<Conta[]>('/contas'),
    ])

    faturaAtualReferencia.value = faturaAtualRes.data
    contas.value = contasRes.data

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

onMounted(carregar)
</script>

<template>
  <div class="min-h-screen bg-base-200 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 class="text-2xl font-bold">Fatura do Cartao</h1>
          <p class="text-sm text-gray-500">Escolha o ciclo para conciliar, ajustar datas e pagar faturas anteriores.</p>
        </div>
        <button class="btn btn-ghost" @click="router.push('/contas')">Voltar</button>
      </div>

      <div v-if="loading" class="text-center py-10">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <template v-else>
        <div v-if="error" class="alert alert-error"><span>{{ error }}</span></div>
        <div v-if="success" class="alert alert-success"><span>{{ success }}</span></div>

        <div class="card bg-base-100 shadow">
          <div class="card-body">
            <div class="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4 md:items-end">
              <div>
                <label class="label"><span class="label-text">Ciclo da fatura</span></label>
                <select v-model="cicloSelecionado" class="select select-bordered w-full" @change="carregarFaturaSelecionada()">
                  <option v-for="opcao in opcoesCiclo" :key="opcao.chave" :value="opcao.chave">
                    {{ opcao.label }}
                  </option>
                </select>
              </div>
              <button class="btn btn-outline" :disabled="carregandoFatura" @click="carregarFaturaSelecionada()">
                <span v-if="carregandoFatura" class="loading loading-spinner loading-sm"></span>
                <span v-else>Recarregar</span>
              </button>
            </div>
          </div>
        </div>

        <div
          v-if="faturaSelecionada"
          class="card bg-base-100 shadow"
          :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'border border-error/20' : 'border border-success/20'"
        >
          <div class="card-body">
            <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 class="card-title">
                  {{ cicloAtualSelecionado ? 'Fatura Atual' : 'Fatura do Ciclo Selecionado' }}
                </h2>
                <p class="text-sm text-gray-500">
                  Use esta visao para conferir os lancamentos do periodo e corrigir datas reais do ciclo.
                </p>
              </div>
              <span class="badge" :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'badge-error' : 'badge-success'">
                {{ (faturaSelecionada.valor_a_pagar || 0) > 0 ? 'A pagar' : 'Quitada' }}
              </span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
              <div class="rounded-box bg-base-200 p-4">
                <p class="text-sm text-gray-500">Periodo do ciclo</p>
                <p class="font-semibold">{{ formatarData(faturaSelecionada.periodo_inicio) }} - {{ formatarData(faturaSelecionada.periodo_fim) }}</p>
                <p class="text-xs text-gray-500 mt-1">Fechamento: {{ formatarData(faturaSelecionada.data_fechamento_fatura) }}</p>
              </div>
              <div class="rounded-box bg-base-200 p-4">
                <p class="text-sm text-gray-500">Vencimento</p>
                <p class="font-semibold">{{ formatarData(faturaSelecionada.data_vencimento_fatura) }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ faturaSelecionada.total_itens }} item(ns)</p>
              </div>
              <div
                class="rounded-box p-4"
                :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'bg-error text-error-content' : 'bg-success text-success-content'"
              >
                <p class="text-sm opacity-80">Total do ciclo</p>
                <p class="text-3xl font-bold">{{ formatarMoeda(faturaSelecionada.valor_total) }}</p>
                <p class="text-xs opacity-80 mt-2">Pago: {{ formatarMoeda(faturaSelecionada.valor_pago || 0) }}</p>
                <p class="text-xs opacity-80">A pagar: {{ formatarMoeda(faturaSelecionada.valor_a_pagar || 0) }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="faturaSelecionada" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Ajuste do Ciclo Selecionado</h2>
            <p class="text-sm text-gray-500">
              Registre aqui excecoes do mes, como feriados, fins de semana ou mudancas operacionais do emissor.
            </p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="label"><span class="label-text">Fechamento previsto</span></label>
                <input :value="faturaSelecionada.data_fechamento_prevista" type="date" class="input input-bordered w-full" disabled />
              </div>
              <div>
                <label class="label"><span class="label-text">Vencimento previsto</span></label>
                <input :value="faturaSelecionada.data_vencimento_prevista" type="date" class="input input-bordered w-full" disabled />
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

        <div v-if="faturaSelecionada" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Pagamento do Ciclo</h2>
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
                <button class="btn btn-primary w-full" :disabled="pagando || !faturaSelecionada || (faturaSelecionada.valor_a_pagar || 0) === 0" @click="pagarFatura">
                  <span v-if="pagando" class="loading loading-spinner loading-sm"></span>
                  <span v-else>Pagar</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="faturaSelecionada" class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title">Lancamentos do Ciclo</h2>
            <div v-if="faturaSelecionada.itens.length === 0" class="text-gray-500 py-6">Nenhum item neste ciclo.</div>
            <div v-else class="space-y-2">
              <div v-for="item in faturaSelecionada.itens" :key="item.transacao_id" class="border rounded-lg p-3 flex items-center justify-between">
                <div>
                  <p class="font-medium">{{ item.descricao }}</p>
                  <p class="text-xs text-gray-500">
                    {{ formatarData(item.data) }}
                    <span v-if="item.data_vencimento"> | Venc: {{ formatarData(item.data_vencimento) }}</span>
                    <span> | {{ item.status_liquidacao }}</span>
                  </p>
                </div>
                <p class="font-bold" :class="item.status_liquidacao === 'liquidado' ? 'text-success' : 'text-error'">
                  {{ formatarMoeda(item.valor_efetivo) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
