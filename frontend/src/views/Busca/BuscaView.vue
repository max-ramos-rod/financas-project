<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { formatDateBR } from '@/utils/date'

const router = useRouter()

interface BuscaTransacao {
  id: number
  descricao: string
  valor: number
  tipo: string
  data: string | null
  status_liquidacao: string | null
  conta_id: number
}

interface BuscaConta {
  id: number
  nome: string
  tipo: string
  saldo: number
}

interface BuscaResultado {
  query: string
  transacoes: BuscaTransacao[]
  contas: BuscaConta[]
}

const termo = ref('')
const resultado = ref<BuscaResultado | null>(null)
const carregando = ref(false)
const erro = ref('')

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const buscar = async (q: string) => {
  if (q.trim().length < 2) {
    resultado.value = null
    return
  }
  carregando.value = true
  erro.value = ''
  try {
    const res = await api.get<BuscaResultado>('/busca', { params: { q: q.trim() } })
    resultado.value = res.data
  } catch (err: any) {
    erro.value = err?.response?.data?.detail || 'Erro ao buscar.'
    resultado.value = null
  } finally {
    carregando.value = false
  }
}

watch(termo, (val) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (val.trim().length < 2) {
    resultado.value = null
    return
  }
  debounceTimer = setTimeout(() => buscar(val), 350)
})

const formatarMoeda = (v: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v)

const corTipo = (tipo: string) =>
  tipo === 'entrada' ? 'text-success' : 'text-error'

const irParaTransacao = (id: number) => router.push(`/transacoes/${id}/editar`)
const irParaConta = (id: number) => router.push(`/contas/${id}/editar`)
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">

      <!-- Page header -->
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-5 lg:mb-6">
        <div>
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight">Busca</h1>
          <p class="text-[10px] sm:text-[11px] font-mono uppercase tracking-widest text-base-content/40 mt-1">
            transações e contas
          </p>
        </div>
      </div>

      <!-- Search input -->
      <div class="card bg-base-100 shadow-sm mb-4">
        <div class="card-body p-3 sm:p-4">
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/30 text-lg">⌕</span>
            <input
              v-model="termo"
              type="search"
              autofocus
              class="input input-bordered w-full pl-10 text-base"
              placeholder="Buscar em transações e contas…"
            />
            <span v-if="carregando" class="absolute right-3 top-1/2 -translate-y-1/2">
              <span class="loading loading-spinner loading-sm"></span>
            </span>
          </div>
          <p class="text-[11px] font-mono text-base-content/40 mt-1">mínimo 2 caracteres · até 10 resultados por tipo</p>
        </div>
      </div>

      <!-- Error -->
      <div v-if="erro" class="alert alert-error mb-4"><span>{{ erro }}</span></div>

      <!-- Empty prompt -->
      <div v-if="!resultado && !carregando && termo.trim().length < 2" class="text-center py-16 text-base-content/30">
        <p class="text-4xl mb-3">⌕</p>
        <p class="font-mono text-sm uppercase tracking-widest">Digite para buscar</p>
      </div>

      <!-- No results -->
      <div
        v-else-if="resultado && resultado.transacoes.length === 0 && resultado.contas.length === 0"
        class="text-center py-16 text-base-content/30"
      >
        <p class="text-4xl mb-3">∅</p>
        <p class="font-mono text-sm uppercase tracking-widest">Nenhum resultado para "{{ resultado.query }}"</p>
      </div>

      <!-- Results -->
      <div v-else-if="resultado" class="flex flex-col gap-4">

        <!-- Transações -->
        <div v-if="resultado.transacoes.length > 0" class="card bg-base-100 shadow-sm">
          <div class="card-body p-0">
            <div class="px-4 pt-4 pb-2">
              <span class="text-[10px] font-mono uppercase tracking-widest text-base-content/50">
                Transações · {{ resultado.transacoes.length }}
              </span>
            </div>
            <div class="divide-y divide-base-200">
              <button
                v-for="t in resultado.transacoes"
                :key="t.id"
                class="w-full flex items-center gap-3 px-4 py-3 hover:bg-base-200 transition-colors text-left"
                @click="irParaTransacao(t.id)"
              >
                <div class="flex-1 min-w-0">
                  <p class="font-medium truncate">{{ t.descricao }}</p>
                  <p class="text-[11px] font-mono text-base-content/50 mt-0.5">
                    {{ t.data ? formatDateBR(t.data) : '—' }}
                    <span v-if="t.status_liquidacao"> · {{ t.status_liquidacao }}</span>
                  </p>
                </div>
                <span :class="['font-mono text-sm font-semibold tabular-nums', corTipo(t.tipo)]">
                  {{ t.tipo === 'entrada' ? '+' : '-' }}{{ formatarMoeda(t.valor) }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <!-- Contas -->
        <div v-if="resultado.contas.length > 0" class="card bg-base-100 shadow-sm">
          <div class="card-body p-0">
            <div class="px-4 pt-4 pb-2">
              <span class="text-[10px] font-mono uppercase tracking-widest text-base-content/50">
                Contas · {{ resultado.contas.length }}
              </span>
            </div>
            <div class="divide-y divide-base-200">
              <button
                v-for="c in resultado.contas"
                :key="c.id"
                class="w-full flex items-center gap-3 px-4 py-3 hover:bg-base-200 transition-colors text-left"
                @click="irParaConta(c.id)"
              >
                <div class="flex-1 min-w-0">
                  <p class="font-medium truncate">{{ c.nome }}</p>
                  <p class="text-[11px] font-mono text-base-content/50 mt-0.5">{{ c.tipo }}</p>
                </div>
                <span class="font-mono text-sm font-semibold tabular-nums">
                  {{ formatarMoeda(c.saldo) }}
                </span>
              </button>
            </div>
          </div>
        </div>

      </div>

    </div>
  </div>
</template>
