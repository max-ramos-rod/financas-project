<script setup lang="ts">
import { computed, ref } from 'vue'
import { Filter } from '@lucide/vue'
import type { Conta, Categoria } from '@/types'
import type { FiltrosTransacoes } from '@/views/Transacoes/transacoesFetch'
import { filtrosPadrao, MESES_ABREV } from '@/composables/useTransacoesFiltros'

interface Props {
  contas: Conta[]
  categorias: Categoria[]
  contadores: { todas: number; entrada: number; saida: number }
}

defineProps<Props>()
const emit = defineEmits<{ limpar: [] }>()

const filtros = defineModel<FiltrosTransacoes>('filtros', { required: true })

const mostrarMaisFiltros = ref(false)

const opcoesPeriodo = computed(() => {
  const hoje = new Date()
  const options = []
  for (let i = -11; i <= 2; i++) {
    const d = new Date(hoje.getFullYear(), hoje.getMonth() + i, 1)
    options.push({
      mes: d.getMonth() + 1,
      ano: d.getFullYear(),
      label: `${MESES_ABREV[d.getMonth()]} ${d.getFullYear()}`,
      value: `${d.getFullYear()}-${d.getMonth() + 1}`,
    })
  }
  return options.reverse()
})

const periodoSelecionado = computed({
  get: () => `${filtros.value.ano}-${filtros.value.mes}`,
  set: (val: string) => {
    const [ano, mes] = val.split('-').map(Number)
    filtros.value.ano = ano
    filtros.value.mes = mes
  },
})

const qtdFiltrosSecundarios = computed(() => {
  const f = filtros.value
  const d = filtrosPadrao()
  return [
    f.status_liquidacao !== d.status_liquidacao,
    f.fixa !== d.fixa,
    f.orcamento !== d.orcamento,
    f.valor_modo !== d.valor_modo,
    f.conta_id !== d.conta_id,
    f.categoria_id !== d.categoria_id,
  ].filter(Boolean).length
})

const temFiltrosAtivos = computed(() => {
  const f = filtros.value
  const d = filtrosPadrao()
  return (
    f.tipo !== d.tipo ||
    f.status_liquidacao !== d.status_liquidacao ||
    f.busca !== d.busca ||
    f.conta_id !== d.conta_id ||
    f.categoria_id !== d.categoria_id ||
    f.fixa !== d.fixa ||
    f.orcamento !== d.orcamento
  )
})
</script>

<template>
  <div class="card bg-base-100 shadow-sm mb-4">
    <div class="card-body p-3 sm:p-4 gap-3">

      <!-- Linha principal -->
      <div class="flex flex-wrap items-center gap-2">

        <!-- Busca -->
        <div class="relative flex-1 min-w-[180px]">
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/30 text-sm">⌕</span>
          <input
            v-model="filtros.busca"
            type="search"
            class="input input-bordered input-sm w-full pl-8"
            placeholder="Buscar descrição…"
          />
        </div>

        <!-- Segmented tipo -->
        <div class="join">
          <button
            class="join-item btn btn-sm"
            :class="filtros.tipo === 'todas' ? 'btn-primary' : 'btn-ghost border border-base-300'"
            @click="filtros.tipo = 'todas'"
          >
            Todas
            <span class="font-mono text-[10px] opacity-60">{{ contadores.todas }}</span>
          </button>
          <button
            class="join-item btn btn-sm"
            :class="filtros.tipo === 'entrada' ? 'btn-success' : 'btn-ghost border border-base-300'"
            @click="filtros.tipo = 'entrada'"
          >
            Entradas
            <span class="font-mono text-[10px] opacity-60">{{ contadores.entrada }}</span>
          </button>
          <button
            class="join-item btn btn-sm"
            :class="filtros.tipo === 'saida' ? 'btn-error' : 'btn-ghost border border-base-300'"
            @click="filtros.tipo = 'saida'"
          >
            Saídas
            <span class="font-mono text-[10px] opacity-60">{{ contadores.saida }}</span>
          </button>
        </div>

        <!-- Período combinado -->
        <select
          v-model="periodoSelecionado"
          class="select select-bordered select-sm w-auto min-w-[120px]"
        >
          <option v-for="op in opcoesPeriodo" :key="op.value" :value="op.value">
            {{ op.label }}
          </option>
        </select>

        <!-- Mais filtros toggle -->
        <button
          class="btn btn-ghost btn-sm gap-1"
          :class="{ 'btn-active': mostrarMaisFiltros }"
          @click="mostrarMaisFiltros = !mostrarMaisFiltros"
        >
          <Filter class="h-3.5 w-3.5" />
          Filtros
          <span v-if="qtdFiltrosSecundarios > 0" class="badge badge-primary badge-xs">
            {{ qtdFiltrosSecundarios }}
          </span>
        </button>

        <!-- Limpar (só quando há filtros) -->
        <button
          v-if="temFiltrosAtivos"
          class="btn btn-ghost btn-sm text-error hidden sm:flex"
          @click="emit('limpar')"
        >
          Limpar
        </button>

      </div>

      <!-- Filtros secundários (expansíveis) -->
      <div
        v-if="mostrarMaisFiltros"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 pt-2 border-t border-base-200"
      >

        <div class="form-control">
          <label class="label py-0 pb-1">
            <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Status</span>
          </label>
          <select v-model="filtros.status_liquidacao" class="select select-bordered select-sm w-full">
            <option value="todos">Todos</option>
            <option value="liquidado">Liquidados</option>
            <option value="previsto">Previstos</option>
            <option value="atrasado">Atrasados</option>
            <option value="cancelado">Cancelados</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label py-0 pb-1">
            <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Conta</span>
          </label>
          <select v-model.number="filtros.conta_id" class="select select-bordered select-sm w-full">
            <option :value="null">Todas</option>
            <option v-for="c in contas" :key="c.id" :value="c.id">{{ c.nome }}</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label py-0 pb-1">
            <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Categoria</span>
          </label>
          <select v-model.number="filtros.categoria_id" class="select select-bordered select-sm w-full">
            <option :value="null">Todas</option>
            <option :value="-1">Sem categoria</option>
            <option v-for="c in categorias" :key="c.id" :value="c.id">{{ c.nome }}</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label py-0 pb-1">
            <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Recorrência</span>
          </label>
          <select v-model="filtros.fixa" class="select select-bordered select-sm w-full">
            <option value="todas">Fixas e não fixas</option>
            <option value="fixas">Apenas fixas</option>
            <option value="nao_fixas">Apenas não fixas</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label py-0 pb-1">
            <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Orçamento</span>
          </label>
          <select v-model="filtros.orcamento" class="select select-bordered select-sm w-full">
            <option value="todos">Todos</option>
            <option value="fora">Fora do orçamento</option>
            <option value="dentro">Dentro do orçamento</option>
          </select>
        </div>

        <div class="form-control sm:col-span-2">
          <label class="label py-0 pb-1">
            <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Valor</span>
          </label>
          <div class="flex gap-2">
            <select v-model="filtros.valor_modo" class="select select-bordered select-sm w-1/2">
              <option value="todos">Qualquer valor</option>
              <option value="igual">Igual a</option>
              <option value="gte">Maior ou igual</option>
              <option value="lte">Menor ou igual</option>
            </select>
            <input
              v-model="filtros.valor_ref"
              class="input input-bordered input-sm w-1/2"
              placeholder="Ex: 500,00"
              :disabled="filtros.valor_modo === 'todos'"
            />
          </div>
        </div>

        <div class="sm:hidden">
          <button
            v-if="temFiltrosAtivos"
            class="btn btn-ghost btn-sm text-error w-full"
            @click="emit('limpar')"
          >
            Limpar filtros
          </button>
        </div>

      </div>

    </div>
  </div>
</template>
