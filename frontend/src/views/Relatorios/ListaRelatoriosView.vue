<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/services/api'
import type { DREMensal } from '@/types'
import EmptyState from '@/components/EmptyState.vue'
import { RefreshCw } from '@lucide/vue'

const loading = ref(false)
const erro = ref('')
const filtros = ref({
  mes: new Date().getMonth() + 1,
  ano: new Date().getFullYear(),
})
const dre = ref<DREMensal | null>(null)

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const carregarDre = async () => {
  loading.value = true
  erro.value = ''
  try {
    const response = await api.get('/relatorios/dre-mensal', {
      params: {
        mes: filtros.value.mes,
        ano: filtros.value.ano,
      },
    })
    dre.value = response.data
  } catch (error: any) {
    erro.value = error?.response?.data?.detail || 'Erro ao carregar relatorio gerencial'
  } finally {
    loading.value = false
  }
}

const exportarCsv = async () => {
  try {
    const response = await api.get('/relatorios/dre-mensal/export', {
      params: {
        mes: filtros.value.mes,
        ano: filtros.value.ano,
      },
      responseType: 'blob',
    })

    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `dre_mensal_${filtros.value.ano}_${String(filtros.value.mes).padStart(2, '0')}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch {
    erro.value = 'Não foi possível exportar o CSV. Tente de novo.'
  }
}

const exportarPdf = async () => {
  try {
    const response = await api.get('/relatorios/dre-mensal/export-pdf', {
      params: {
        mes: filtros.value.mes,
        ano: filtros.value.ano,
      },
      responseType: 'blob',
    })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `dre_mensal_${filtros.value.ano}_${String(filtros.value.mes).padStart(2, '0')}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch {
    erro.value = 'Não foi possível exportar o PDF. Tente de novo.'
  }
}

onMounted(() => {
  carregarDre()
})
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <div class="container mx-auto px-4 py-6 space-y-6">
      <div class="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 class="text-xl font-semibold">Relatórios</h1>
          <p class="text-sm text-base-content/50">DRE mensal: Entradas, Saídas, Resultado e Pago × Previsto</p>
        </div>
      </div>

      <div class="card bg-base-100 shadow-sm">
        <div class="card-body py-3">
          <div class="flex flex-wrap items-end gap-2">
            <div>
              <label class="label pb-1"><span class="label-text text-xs font-mono uppercase tracking-widest text-base-content/50">Mês</span></label>
              <select v-model.number="filtros.mes" class="select select-bordered select-sm">
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
            <div>
              <label class="label pb-1"><span class="label-text text-xs font-mono uppercase tracking-widest text-base-content/50">Ano</span></label>
              <input v-model.number="filtros.ano" type="number" min="2000" max="2100" class="input input-bordered input-sm w-24" />
            </div>
            <button class="btn btn-primary btn-sm" :disabled="loading" @click="carregarDre">{{ loading ? 'Carregando...' : 'Atualizar' }}</button>
            <button class="btn btn-outline btn-sm" :disabled="loading || !dre" @click="exportarCsv">Exportar CSV</button>
            <button class="btn btn-outline btn-sm" :disabled="loading || !dre" @click="exportarPdf">Exportar PDF</button>
          </div>
        </div>
      </div>

      <EmptyState
        v-if="!loading && erro"
        variant="error"
        title="Não foi possível carregar."
        :description="erro"
      >
        <template #icon><RefreshCw /></template>
        <template #actions>
          <button class="btn btn-primary btn-sm" @click="carregarDre">Tentar de novo</button>
        </template>
      </EmptyState>

      <div v-if="loading" class="text-center py-16">
        <span class="loading loading-spinner loading-lg"></span>
      </div>

      <template v-else-if="dre">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <p class="text-xs font-mono uppercase tracking-widest text-base-content/50">Entradas (Total)</p>
              <p class="text-3xl text-success font-bold tabular-nums">{{ formatarMoeda(dre.entradas_total) }}</p>
            </div>
          </div>
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <p class="text-xs font-mono uppercase tracking-widest text-base-content/50">Saídas (Total)</p>
              <p class="text-3xl text-error font-bold tabular-nums">{{ formatarMoeda(dre.saidas_total) }}</p>
            </div>
          </div>
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <p class="text-xs font-mono uppercase tracking-widest text-base-content/50">Resultado (Total)</p>
              <p :class="['text-3xl font-bold tabular-nums', dre.resultado_total >= 0 ? 'text-success' : 'text-error']">
                {{ formatarMoeda(dre.resultado_total) }}
              </p>
            </div>
          </div>
        </div>

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title">Pago x Previsto</h2>
            <div class="overflow-x-auto">
              <table class="table">
                <thead>
                  <tr>
                    <th>Indicador</th>
                    <th class="text-right">Entradas</th>
                    <th class="text-right">Saídas</th>
                    <th class="text-right">Resultado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Liquidado (Pago/Recebido)</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.entradas_liquidadas) }}</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.saidas_liquidadas) }}</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.resultado_liquidado) }}</td>
                  </tr>
                  <tr>
                    <td>Previsto (Aberto)</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.entradas_previstas) }}</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.saidas_previstas) }}</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.resultado_previsto) }}</td>
                  </tr>
                  <tr class="font-semibold">
                    <td>Total do período</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.entradas_total) }}</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.saidas_total) }}</td>
                    <td class="text-right tabular-nums">{{ formatarMoeda(dre.resultado_total) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <h2 class="card-title">Entradas por categoria</h2>
              <div class="overflow-x-auto">
                <table class="table table-zebra">
                  <thead>
                    <tr>
                      <th>Categoria</th>
                      <th class="text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="dre.entradas_por_categoria.length === 0">
                      <td colspan="2" class="text-center opacity-60">Sem entradas no período</td>
                    </tr>
                    <tr v-for="item in dre.entradas_por_categoria" :key="`in-${item.categoria_id ?? 'none'}-${item.categoria_nome}`">
                      <td>{{ item.categoria_nome }}</td>
                      <td class="text-right tabular-nums">{{ formatarMoeda(item.valor) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div class="card bg-base-100 shadow-sm">
            <div class="card-body">
              <h2 class="card-title">Saídas por categoria</h2>
              <div class="overflow-x-auto">
                <table class="table table-zebra">
                  <thead>
                    <tr>
                      <th>Categoria</th>
                      <th class="text-right">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="dre.saidas_por_categoria.length === 0">
                      <td colspan="2" class="text-center opacity-60">Sem saídas no período</td>
                    </tr>
                    <tr v-for="item in dre.saidas_por_categoria" :key="`out-${item.categoria_id ?? 'none'}-${item.categoria_nome}`">
                      <td>{{ item.categoria_nome }}</td>
                      <td class="text-right tabular-nums">{{ formatarMoeda(item.valor) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
