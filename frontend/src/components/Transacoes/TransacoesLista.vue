<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Conta, Categoria, Transacao } from '@/types'
import { formatDateBR } from '@/utils/date'
import { valorEfetivo, formatarMoeda } from '@/utils/financeiro'
import { LABELS } from '@/utils/strings'
import EmptyState from '@/components/ui/EmptyState.vue'
import { List, Filter, Pencil, Copy, CircleCheck, Receipt, Trash2, X } from '@lucide/vue'

interface Props {
  transacoes: Transacao[]
  contas: Conta[]
  categorias: Categoria[]
  temFiltrosAtivos: boolean
  duplicandoId: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'limpar-filtros': []
  'nova-transacao': []
  'editar-transacao': [id: number]
  'duplicar-transacao': [id: number]
  'iniciar-liquidacao': [t: Transacao]
  'iniciar-delecao': [t: Transacao]
  'abrir-fatura-cartao': [t: Transacao]
  'bulk-excluir': [ids: number[]]
  'bulk-liquidar': [ids: number[]]
}>()

// --- Seleção múltipla ---
const selectedIds = ref<Set<number>>(new Set())

const isSelected = (id: number) => selectedIds.value.has(id)

const toggleSelect = (id: number) => {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

const selectAll = () => {
  selectedIds.value = new Set(props.transacoes.map((t) => t.id))
}

const clearSelection = () => {
  selectedIds.value = new Set()
}

const allSelected = computed(
  () => props.transacoes.length > 0 && props.transacoes.every((t) => selectedIds.value.has(t.id)),
)

const someSelected = computed(() => selectedIds.value.size > 0)

const hasLiquidaveis = computed(() =>
  [...selectedIds.value].some((id) => {
    const t = props.transacoes.find((t) => t.id === id)
    return (
      t &&
      (t.status_liquidacao || 'liquidado') !== 'liquidado' &&
      !isContaCartaoCredito(t.conta_id, props.contas)
    )
  }),
)

defineExpose({ clearSelection })

// --- Helpers ---
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
          class="px-4 py-3 transition-colors"
          :class="isSelected(t.id) ? 'bg-base-200/50' : 'active:bg-base-200'"
        >
          <!-- Linha 1: Checkbox + Data | Status -->
          <div class="flex items-center justify-between mb-1">
            <div class="flex items-center gap-2">
              <input
                type="checkbox"
                class="checkbox checkbox-xs"
                :checked="isSelected(t.id)"
                @change="toggleSelect(t.id)"
              />
              <span class="font-mono text-[11px] tabular-nums text-base-content/40">
                {{ formatarData(t.data) }}
              </span>
            </div>
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
                class="btn btn-ghost btn-xs text-primary tooltip"
                data-tip="Ver fatura"
                @click="emit('abrir-fatura-cartao', t)"
              >
                <Receipt :size="13" />
              </button>
              <template v-else>
                <button class="btn btn-ghost btn-xs tooltip" data-tip="Editar" @click="emit('editar-transacao', t.id)">
                  <Pencil :size="13" />
                </button>
                <button
                  class="btn btn-ghost btn-xs tooltip"
                  :data-tip="duplicandoId === t.id ? '' : 'Copiar'"
                  :disabled="duplicandoId === t.id"
                  @click="emit('duplicar-transacao', t.id)"
                >
                  <span v-if="duplicandoId === t.id" class="loading loading-spinner loading-xs"></span>
                  <Copy v-else :size="13" />
                </button>
                <button
                  v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id, contas)"
                  class="btn btn-ghost btn-xs text-success tooltip"
                  :data-tip="t.tipo === 'entrada' ? 'Receber' : 'Pagar'"
                  @click="emit('iniciar-liquidacao', t)"
                >
                  <CircleCheck :size="13" />
                </button>
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
            <input
              type="checkbox"
              class="checkbox checkbox-xs shrink-0"
              :checked="allSelected"
              :indeterminate="someSelected && !allSelected"
              @change="allSelected ? clearSelection() : selectAll()"
            />
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
            class="group flex items-stretch gap-3 px-5 py-3 transition-colors"
            :class="isSelected(t.id) ? 'bg-base-200/30' : 'hover:bg-base-50'"
          >
            <!-- Checkbox -->
            <div class="flex items-center shrink-0">
              <input
                type="checkbox"
                class="checkbox checkbox-xs"
                :checked="isSelected(t.id)"
                @change="toggleSelect(t.id)"
              />
            </div>

            <!-- Conteúdo 2 linhas -->
            <div class="flex-1 min-w-0">
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

              <!-- Linha 2: Status · Conta · Categoria · Botões -->
              <div class="flex items-center gap-3 mt-1">
                <span :class="['flex items-center gap-1 font-mono text-[10px] uppercase tracking-wide shrink-0 w-[68px]', statusColor(t)]">
                  <span class="w-1 h-1 rounded-full bg-current shrink-0"></span>
                  {{ statusLabel(t, contas) }}
                </span>
                <span class="text-xs text-base-content/40 flex-1 min-w-0 truncate">
                  {{ isFaturaCartao(t)
                    ? `${getContaNome(t.conta_id, contas)} · ${t.fatura_total_itens || 0} itens`
                    : `${getContaNome(t.conta_id, contas)} · ${getCategoriaNome(t.categoria_id, categorias)}` }}
                </span>
                <div class="flex gap-1 shrink-0">
                  <button
                    v-if="isFaturaCartao(t)"
                    class="btn btn-ghost btn-xs text-primary tooltip"
                    data-tip="Ver fatura"
                    @click="emit('abrir-fatura-cartao', t)"
                  >
                    <Receipt :size="13" />
                  </button>
                  <template v-else>
                    <button class="btn btn-ghost btn-xs tooltip" data-tip="Editar" @click="emit('editar-transacao', t.id)">
                      <Pencil :size="13" />
                    </button>
                    <button
                      class="btn btn-ghost btn-xs tooltip"
                      :data-tip="duplicandoId === t.id ? '' : 'Copiar'"
                      :disabled="duplicandoId === t.id"
                      @click="emit('duplicar-transacao', t.id)"
                    >
                      <span v-if="duplicandoId === t.id" class="loading loading-spinner loading-xs"></span>
                      <Copy v-else :size="13" />
                    </button>
                    <button
                      v-if="(t.status_liquidacao || 'liquidado') !== 'liquidado' && !isContaCartaoCredito(t.conta_id, contas)"
                      class="btn btn-ghost btn-xs text-success tooltip"
                      :data-tip="t.tipo === 'entrada' ? 'Receber' : 'Pagar'"
                      @click="emit('iniciar-liquidacao', t)"
                    >
                      <CircleCheck :size="13" />
                    </button>
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
          v-if="hasLiquidaveis"
          class="btn btn-ghost btn-sm gap-1.5 text-success"
          @click="emit('bulk-liquidar', [...selectedIds])"
        >
          <CircleCheck :size="15" />
          Liquidar
        </button>
        <button
          class="btn btn-ghost btn-sm gap-1.5 text-error"
          @click="emit('bulk-excluir', [...selectedIds])"
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
