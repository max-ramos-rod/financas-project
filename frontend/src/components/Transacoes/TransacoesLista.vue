<script setup lang="ts">
import type { Conta, Categoria, Transacao } from '@/types'
import { formatDateBR } from '@/utils/date'
import { valorEfetivo, formatarMoeda } from '@/utils/financeiro'
import { LABELS } from '@/utils/strings'
import EmptyState from '@/components/ui/EmptyState.vue'
import { List, Filter } from '@lucide/vue'

interface Props {
  transacoes: Transacao[]
  contas: Conta[]
  categorias: Categoria[]
  temFiltrosAtivos: boolean
  duplicandoId: number | null
}

defineProps<Props>()

const emit = defineEmits<{
  'limpar-filtros': []
  'nova-transacao': []
  'editar-transacao': [id: number]
  'duplicar-transacao': [id: number]
  'iniciar-liquidacao': [t: Transacao]
  'iniciar-delecao': [t: Transacao]
  'abrir-fatura-cartao': [t: Transacao]
}>()

const formatarData = (data: string) => formatDateBR(data)

const getContaNome = (id: number, contas: Conta[]) =>
  contas.find((c) => c.id === id)?.nome || 'Conta'

const getCategoriaNome = (id: number | null, categorias: Categoria[]) =>
  categorias.find((c) => c.id === id)?.nome || LABELS.sem_categoria

const isContaCartaoCredito = (contaId: number, contas: Conta[]) =>
  contas.find((c) => c.id === contaId)?.tipo === 'cartao_credito'

const isFaturaCartao = (t: Transacao) => t.item_tipo === 'fatura_cartao'

const statusLabel = (t: Transacao, contas: Conta[]) => {
  const s = t.status_liquidacao || 'liquidado'
  if (s === 'liquidado') return t.tipo === 'entrada' ? LABELS.recebido : LABELS.pago
  if (s === 'previsto')
    return t.tipo === 'entrada'
      ? LABELS.a_receber
      : isContaCartaoCredito(t.conta_id, contas)
        ? 'Fatura'
        : LABELS.a_pagar
  if (s === 'atrasado') return LABELS.st_atrasado
  return LABELS.st_cancelado
}

const statusColor = (t: Transacao) => {
  const s = t.status_liquidacao || 'liquidado'
  if (s === 'liquidado') return 'text-ok'
  if (s === 'atrasado') return 'text-crit'
  return 'text-warn'
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm">

    <!-- Empty state -->
    <div v-if="transacoes.length === 0" class="card-body py-12">
      <EmptyState
        v-if="temFiltrosAtivos"
        variant="filtered"
        title="Nenhuma transação encontrada."
        description="Tente ajustar os filtros para ver mais resultados."
      >
        <template #icon><Filter /></template>
        <template #actions>
          <button class="btn btn-ghost btn-sm" @click="emit('limpar-filtros')">Limpar filtros</button>
        </template>
      </EmptyState>
      <EmptyState
        v-else
        variant="first-time"
        title="Ainda nada por aqui."
        description="Sua primeira transação aparece quando você lança uma entrada, pagamento ou saldo inicial."
      >
        <template #icon><List /></template>
        <template #actions>
          <button class="btn btn-primary btn-sm" @click="emit('nova-transacao')">
            {{ LABELS.nova_transacao }}
          </button>
        </template>
      </EmptyState>
    </div>

    <template v-else>

      <!-- TILES — 3 linhas (< lg, 0–1023px) -->
      <div class="lg:hidden divide-y divide-base-200 overflow-x-hidden">
        <div
          v-for="t in transacoes"
          :key="`m-${t.id}`"
          class="px-4 py-3 active:bg-base-200 transition-colors"
        >
          <!-- Linha 1: Data | Status -->
          <div class="flex items-center justify-between mb-1">
            <span class="font-mono text-[11px] tabular-nums text-base-content/40">
              {{ formatarData(t.data) }}
            </span>
            <span :class="['flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide', statusColor(t)]">
              <span class="w-1 h-1 rounded-full bg-current"></span>
              {{ statusLabel(t, contas) }}
            </span>
          </div>

          <!-- Linha 2: Dot + Descrição + Parcela | Valor -->
          <div class="flex items-start justify-between gap-3 mb-1">
            <div class="min-w-0 flex-1 flex items-center gap-1.5">
              <span
                :class="[
                  'shrink-0 w-1.5 h-1.5 rounded-full mt-0.5',
                  isFaturaCartao(t) ? 'bg-warning' :
                  t.tipo === 'entrada' ? 'bg-success' : 'bg-error'
                ]"
              ></span>
              <span class="font-medium text-sm truncate">{{ t.descricao }}</span>
              <span
                v-if="t.parcelado && t.parcela_atual && t.total_parcelas"
                class="font-mono text-[10px] text-base-content/40 shrink-0"
              >
                {{ t.parcela_atual }}/{{ t.total_parcelas }}
              </span>
            </div>
            <span
              :class="[
                'font-semibold text-sm tabular-nums whitespace-nowrap shrink-0',
                t.tipo === 'entrada' ? 'text-success' : 'text-base-content'
              ]"
            >
              {{ t.tipo === 'entrada' ? '+' : '−' }} {{ formatarMoeda(valorEfetivo(t)).replace('R$ ', '') }}
            </span>
          </div>

          <!-- Linha 3: Conta · Categoria | Botões -->
          <div class="flex items-center justify-between gap-2 overflow-hidden">
            <span class="text-xs text-base-content/40 truncate min-w-0 flex-1">
              {{ getContaNome(t.conta_id, contas) }}
              <template v-if="!isFaturaCartao(t)"> · {{ getCategoriaNome(t.categoria_id, categorias) }}</template>
            </span>
            <div class="flex gap-1 shrink-0">
              <button
                v-if="isFaturaCartao(t)"
                class="btn btn-ghost btn-xs text-primary"
                @click="emit('abrir-fatura-cartao', t)"
              >Fatura</button>
              <template v-else>
                <button class="btn btn-ghost btn-xs" @click="emit('editar-transacao', t.id)">Editar</button>
                <button
                  v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id, contas)"
                  class="btn btn-ghost btn-xs text-success"
                  @click="emit('iniciar-liquidacao', t)"
                >OK</button>
                <button
                  class="btn btn-ghost btn-xs text-error"
                  @click="emit('iniciar-delecao', t)"
                >×</button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- DESKTOP — 2 linhas por item, sem scroll horizontal (≥ lg, 1024px+) -->
      <div class="hidden lg:block">
        <!-- Cabeçalho -->
        <div class="px-5 py-2 border-b border-base-200">
          <div class="flex items-center gap-3 text-[10px] font-mono uppercase tracking-widest text-base-content/40">
            <span class="shrink-0 w-[68px]">Data</span>
            <span class="flex-1">Descrição</span>
            <span class="shrink-0">Valor</span>
          </div>
        </div>

        <!-- Linhas -->
        <div class="divide-y divide-base-200">
          <div
            v-for="t in transacoes"
            :key="t.id"
            class="group px-5 py-3 hover:bg-base-50 transition-colors"
          >
            <!-- Linha 1: Data · Descrição + Parcela · Valor -->
            <div class="flex items-center gap-3">
              <span class="font-mono text-[12px] tabular-nums text-base-content/50 shrink-0 w-[68px]">
                {{ formatarData(t.data) }}
              </span>
              <div class="flex items-center gap-2 flex-1 min-w-0">
                <span
                  :class="[
                    'shrink-0 w-1.5 h-1.5 rounded-full',
                    isFaturaCartao(t) ? 'bg-warning' :
                    t.tipo === 'entrada' ? 'bg-success' : 'bg-error'
                  ]"
                ></span>
                <span class="font-medium text-sm truncate">{{ t.descricao }}</span>
                <span
                  v-if="t.parcelado && t.parcela_atual && t.total_parcelas"
                  class="font-mono text-[10px] text-base-content/40 shrink-0"
                >
                  {{ t.parcela_atual }}/{{ t.total_parcelas }}
                </span>
              </div>
              <span
                :class="[
                  'font-semibold text-sm tabular-nums whitespace-nowrap shrink-0',
                  t.tipo === 'entrada' ? 'text-success' : 'text-base-content'
                ]"
              >
                {{ t.tipo === 'entrada' ? '+ ' : '− ' }}{{ formatarMoeda(valorEfetivo(t)).replace('R$ ', '') }}
              </span>
            </div>

            <!-- Linha 2: Conta · Categoria · Status · Botões (hover) -->
            <!-- pl-20 = 80px alinha sob o dot da linha 1 (68px data + 12px gap) -->
            <div class="flex items-center gap-3 mt-1 pl-20">
              <span class="text-xs text-base-content/40 flex-1 min-w-0 truncate">
                {{ isFaturaCartao(t)
                  ? `${getContaNome(t.conta_id, contas)} · ${t.fatura_total_itens || 0} itens`
                  : `${getContaNome(t.conta_id, contas)} · ${getCategoriaNome(t.categoria_id, categorias)}` }}
              </span>
              <span :class="['flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide shrink-0', statusColor(t)]">
                <span class="w-1 h-1 rounded-full bg-current shrink-0"></span>
                {{ statusLabel(t, contas) }}
              </span>
              <div class="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  v-if="isFaturaCartao(t)"
                  class="btn btn-ghost btn-xs text-primary"
                  @click="emit('abrir-fatura-cartao', t)"
                >Fatura</button>
                <template v-else>
                  <button class="btn btn-ghost btn-xs" @click="emit('editar-transacao', t.id)">Editar</button>
                  <button
                    class="btn btn-ghost btn-xs"
                    :disabled="duplicandoId === t.id"
                    @click="emit('duplicar-transacao', t.id)"
                  >
                    <span v-if="duplicandoId === t.id" class="loading loading-spinner loading-xs"></span>
                    <span v-else>Copiar</span>
                  </button>
                  <button
                    v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id, contas)"
                    class="btn btn-ghost btn-xs text-success"
                    @click="emit('iniciar-liquidacao', t)"
                  >OK</button>
                  <button
                    class="btn btn-ghost btn-xs text-error"
                    @click="emit('iniciar-delecao', t)"
                  >×</button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Rodapé da lista -->
      <div class="px-5 py-3 border-t border-base-200 flex justify-between items-center">
        <span class="font-mono text-[11px] text-base-content/40">
          {{ transacoes.length }} {{ transacoes.length === 1 ? 'lançamento' : 'lançamentos' }}
        </span>
        <button
          v-if="temFiltrosAtivos"
          class="btn btn-ghost btn-xs text-error lg:hidden"
          @click="emit('limpar-filtros')"
        >
          Limpar filtros
        </button>
      </div>

    </template>
  </div>
</template>
