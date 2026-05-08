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

type Aba = 'ajuste' | 'pagamento'
const abaAtiva = ref<Aba>('ajuste')

// Modal de exclusão
const modalExcluirAberta = ref(false)
const transacaoParaExcluir = ref<{ id: number; descricao: string; valor: number } | null>(null)
const excluindo = ref(false)

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
      label: `${formatarMesAno(ano, mes)}${deslocamento === 0 ? ' (atual)' : ''}`,
    }
  }).reverse()
})

const cicloAtualSelecionado = computed(() =>
  Boolean(faturaAtualReferencia.value && cicloSelecionado.value === chaveCiclo(
    faturaAtualReferencia.value.competencia_ano,
    faturaAtualReferencia.value.competencia_mes
  ))
)

const novaTransacao = () => {
  router.push({
    path: '/transacoes/nova',
    query: {
      conta_id: contaId,
      ano: faturaSelecionada.value?.competencia_ano,
      mes: faturaSelecionada.value?.competencia_mes,
      tipo: 'saida',
    },
  })
}

const abrirModalExcluir = (id: number, descricao: string, valor: number) => {
  transacaoParaExcluir.value = { id, descricao, valor }
  modalExcluirAberta.value = true
}

const fecharModalExcluir = () => {
  modalExcluirAberta.value = false
  transacaoParaExcluir.value = null
}

const confirmarExclusao = async () => {
  if (!transacaoParaExcluir.value) return
  excluindo.value = true
  try {
    await api.delete(`/transacoes/${transacaoParaExcluir.value.id}`)
    await carregarFaturaSelecionada(true)
    fecharModalExcluir()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Erro ao excluir transação.'
    fecharModalExcluir()
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
  <div class="min-h-screen bg-base-200 p-4 md:p-6">
    <div class="max-w-3xl mx-auto space-y-4">

      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold">Fatura do Cartão</h1>
          <p class="text-xs text-base-content/50">Concilie, ajuste datas e pague faturas</p>
        </div>
        <button class="btn btn-ghost btn-sm" @click="router.push('/contas')">← Voltar</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <template v-else>

        <!-- Alertas -->
        <div v-if="error" class="alert alert-error py-2 text-sm"><span>{{ error }}</span></div>
        <div v-if="success" class="alert alert-success py-2 text-sm"><span>{{ success }}</span></div>

        <!-- Seletor de ciclo -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body p-4">
            <div class="flex gap-2 items-end">
              <div class="flex-1">
                <label class="label py-0 pb-1">
                  <span class="label-text text-xs font-medium text-base-content/60 uppercase tracking-wide">Ciclo da fatura</span>
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
                class="btn btn-outline btn-sm"
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

          <!-- Resumo da fatura -->
          <div
            class="card shadow-sm"
            :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'bg-error text-error-content' : 'bg-success text-success-content'"
          >
            <div class="card-body p-4">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="text-xs font-medium opacity-70 uppercase tracking-wide">
                    {{ cicloAtualSelecionado ? 'Fatura Atual' : 'Ciclo Selecionado' }}
                  </p>
                  <p class="text-3xl font-bold mt-0.5">{{ formatarMoeda(faturaSelecionada.valor_total) }}</p>
                  <p class="text-xs opacity-70 mt-1">
                    {{ faturaSelecionada.total_itens }} item(ns) &nbsp;·&nbsp;
                    Venc. {{ formatarData(faturaSelecionada.data_vencimento_fatura) }}
                  </p>
                </div>
                <span
                  class="badge badge-lg"
                  :class="(faturaSelecionada.valor_a_pagar || 0) > 0 ? 'badge-error border-error-content/30' : 'badge-success border-success-content/30'"
                >
                  {{ (faturaSelecionada.valor_a_pagar || 0) > 0 ? 'A pagar' : 'Quitada' }}
                </span>
              </div>
              <div class="divider my-1 opacity-30"></div>
              <div class="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <p class="opacity-60">Período</p>
                  <p class="font-medium">{{ formatarData(faturaSelecionada.periodo_inicio) }}</p>
                  <p class="font-medium">{{ formatarData(faturaSelecionada.periodo_fim) }}</p>
                </div>
                <div>
                  <p class="opacity-60">Fechamento</p>
                  <p class="font-medium">{{ formatarData(faturaSelecionada.data_fechamento_fatura) }}</p>
                </div>
                <div>
                  <p class="opacity-60">Pago / A pagar</p>
                  <p class="font-medium">{{ formatarMoeda(faturaSelecionada.valor_pago || 0) }}</p>
                  <p class="font-medium">{{ formatarMoeda(faturaSelecionada.valor_a_pagar || 0) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Abas: Ajuste do Ciclo | Pagamento -->
          <div class="card bg-base-100 shadow-sm">
            <div class="border-b border-base-200">
              <div role="tablist" class="tabs tabs-bordered px-4">
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
                  <span
                    v-if="(faturaSelecionada.valor_a_pagar || 0) > 0"
                    class="badge badge-xs badge-error"
                  >!</span>
                </button>
              </div>
            </div>

            <!-- Aba: Ajuste do Ciclo -->
            <div v-if="abaAtiva === 'ajuste'" class="card-body p-4 space-y-3">
              <p class="text-xs text-base-content/50">
                Registre exceções do mês: feriados, fins de semana ou mudanças operacionais do emissor.
              </p>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="label py-0 pb-1"><span class="label-text text-xs">Fechamento previsto</span></label>
                  <input :value="faturaSelecionada.data_fechamento_prevista" type="date" class="input input-bordered input-sm w-full" disabled />
                </div>
                <div>
                  <label class="label py-0 pb-1"><span class="label-text text-xs">Vencimento previsto</span></label>
                  <input :value="faturaSelecionada.data_vencimento_prevista" type="date" class="input input-bordered input-sm w-full" disabled />
                </div>
                <div>
                  <label class="label py-0 pb-1"><span class="label-text text-xs">Fechamento real</span></label>
                  <input v-model="dataFechamentoReal" type="date" class="input input-bordered input-sm w-full" />
                </div>
                <div>
                  <label class="label py-0 pb-1"><span class="label-text text-xs">Vencimento real</span></label>
                  <input v-model="dataVencimentoReal" type="date" class="input input-bordered input-sm w-full" />
                </div>
              </div>
              <div>
                <label class="label py-0 pb-1"><span class="label-text text-xs">Observação</span></label>
                <textarea
                  v-model="observacaoCiclo"
                  class="textarea textarea-bordered textarea-sm w-full"
                  rows="2"
                  placeholder="Ex.: banco postergou vencimento por feriado nacional."
                ></textarea>
              </div>
              <div class="flex gap-2 justify-end pt-1">
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
            <div v-if="abaAtiva === 'pagamento'" class="card-body p-4 space-y-3">
              <p class="text-xs text-base-content/50">
                {{ (faturaSelecionada.valor_a_pagar || 0) > 0
                  ? `Valor em aberto: ${formatarMoeda(faturaSelecionada.valor_a_pagar || 0)}`
                  : 'Esta fatura já está quitada.' }}
              </p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="label py-0 pb-1"><span class="label-text text-xs">Conta de pagamento</span></label>
                  <select v-model.number="contaPagamentoId" class="select select-bordered select-sm w-full">
                    <option :value="null">Selecione</option>
                    <option v-for="conta in contasPagamento" :key="conta.id" :value="conta.id">
                      {{ conta.nome }} ({{ formatarMoeda(conta.saldo) }})
                    </option>
                  </select>
                </div>
                <div>
                  <label class="label py-0 pb-1"><span class="label-text text-xs">Data de pagamento</span></label>
                  <input v-model="dataPagamento" type="date" class="input input-bordered input-sm w-full" />
                </div>
              </div>
              <div class="flex justify-end pt-1">
                <button
                  class="btn btn-primary btn-sm"
                  :disabled="pagando || (faturaSelecionada.valor_a_pagar || 0) === 0"
                  @click="pagarFatura"
                >
                  <span v-if="pagando" class="loading loading-spinner loading-xs"></span>
                  <span v-else>Confirmar pagamento</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Lista de lançamentos -->
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body p-4">
              <div class="flex items-center justify-between mb-3">
                <div>
                  <p class="font-semibold text-sm">Lançamentos do Ciclo</p>
                  <p class="text-xs text-base-content/40">
                    {{ faturaSelecionada.itens.length === 0 ? 'Nenhum lançamento' : `${faturaSelecionada.itens.length} lançamento(s)` }}
                  </p>
                </div>
                <button class="btn btn-primary btn-sm" @click="novaTransacao">+ Nova transação</button>
              </div>

              <div v-if="faturaSelecionada.itens.length === 0" class="text-center py-10 text-base-content/30 text-sm">
                Nenhum lançamento neste ciclo.
              </div>

              <template v-else>

                <!-- Desktop: tabela nativa -->
                <div class="hidden md:block overflow-x-auto">
                  <table class="table table-sm w-full">
                    <thead>
                      <tr class="text-xs text-base-content/40 uppercase tracking-wide border-b border-base-200">
                        <th class="font-medium pl-0">Descrição</th>
                        <th class="font-medium">Data</th>
                        <th class="font-medium">Vencimento</th>
                        <th class="font-medium">Status</th>
                        <th class="font-medium text-right pr-0">Valor</th>
                        <th class="w-8"></th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-base-200">
                      <tr
                        v-for="item in faturaSelecionada.itens"
                        :key="item.transacao_id"
                        class="hover:bg-base-50"
                      >
                        <td class="pl-0 font-medium text-sm max-w-[200px] truncate">{{ item.descricao }}</td>
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
                        <td class="text-right pr-0 font-bold text-sm whitespace-nowrap"
                          :class="item.status_liquidacao === 'liquidado' ? 'text-success' : 'text-error'"
                        >
                          {{ formatarMoeda(item.valor_efetivo) }}
                        </td>
                        <td class="pr-0">
                          <button
                            class="btn btn-ghost btn-xs text-error opacity-30 hover:opacity-100"
                            @click="abrirModalExcluir(item.transacao_id, item.descricao, item.valor_efetivo)"
                          >✕</button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <!-- Mobile: cards por item -->
                <div class="md:hidden divide-y divide-base-200">
                  <div
                    v-for="item in faturaSelecionada.itens"
                    :key="item.transacao_id"
                    class="py-3 flex items-start justify-between gap-3"
                  >
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium truncate">{{ item.descricao }}</p>
                      <p class="text-xs text-base-content/50 mt-0.5">
                        {{ formatarData(item.data) }}
                        <span v-if="item.data_vencimento"> · Venc. {{ formatarData(item.data_vencimento) }}</span>
                      </p>
                        <span
                          class="badge badge-sm whitespace-nowrap"
                          :class="item.status_liquidacao === 'liquidado' ? 'badge-success' : 'badge-warning'"
                        >{{ item.status_liquidacao }}</span>
                    </div>
                    <div class="flex items-center gap-2 shrink-0">
                      <p
                        class="text-sm font-bold"
                        :class="item.status_liquidacao === 'liquidado' ? 'text-success' : 'text-error'"
                      >
                        {{ formatarMoeda(item.valor_efetivo) }}
                      </p>
                      <button
                        class="btn btn-ghost btn-xs text-error opacity-30 hover:opacity-100"
                        @click="abrirModalExcluir(item.transacao_id, item.descricao, item.valor_efetivo)"
                      >✕</button>
                    </div>
                  </div>
                </div>

                <!-- Rodapé total -->
                <div class="flex justify-between items-center pt-3 mt-1 border-t border-base-200">
                  <span class="text-xs text-base-content/40">Total do ciclo</span>
                  <span class="text-base font-bold">{{ formatarMoeda(faturaSelecionada.valor_total) }}</span>
                </div>

              </template>
            </div>
          </div>

        </template>
      </template>
    </div>
  </div>

  <!-- Modal de confirmação de exclusão -->
  <dialog :open="modalExcluirAberta" class="modal modal-bottom sm:modal-middle">
    <div class="modal-box">
      <h3 class="font-bold text-base">Excluir transação?</h3>
      <div v-if="transacaoParaExcluir" class="mt-3 rounded-lg bg-base-200 p-3">
        <p class="text-sm font-medium">{{ transacaoParaExcluir.descricao }}</p>
        <p class="text-sm text-error font-bold mt-0.5">{{ formatarMoeda(transacaoParaExcluir.valor) }}</p>
      </div>
      <p class="text-xs text-base-content/50 mt-3">Esta ação não pode ser desfeita.</p>
      <div class="modal-action mt-4">
        <button class="btn btn-ghost btn-sm" :disabled="excluindo" @click="fecharModalExcluir">Cancelar</button>
        <button class="btn btn-error btn-sm" :disabled="excluindo" @click="confirmarExclusao">
          <span v-if="excluindo" class="loading loading-spinner loading-xs"></span>
          <span v-else>Excluir</span>
        </button>
      </div>
    </div>
    <div class="modal-backdrop bg-black/40" @click="fecharModalExcluir"></div>
  </dialog>
</template>