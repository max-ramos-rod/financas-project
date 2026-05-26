<script setup lang="ts">
/**
 * OrcamentoComparativoChart · Versão HTML/CSS pura
 * ----------------------------------------------------------------------------
 * Lista categoria × planejado × gasto, com barra de progresso.
 * Indica visualmente quando estoura (barra vermelha cheia + alerta).
 * Não usa ApexCharts — segue o padrão do mockup `05-Dashboard Reformulado.html`.
 */

import { computed } from 'vue'

const props = defineProps<{
  dados: { categoria: string; planejado: number; gasto: number; estourado?: boolean }[]
}>()

const formatarMoeda = (valor: number): string =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)

const formatarCompacto = (valor: number): string => {
  if (valor >= 1000) {
    const k = valor / 1000
    return `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: k >= 10 ? 0 : 1 }).format(k)}k`
  }
  return `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 }).format(valor)}`
}

const linhas = computed(() =>
  props.dados.map(d => {
    const percentual = d.planejado > 0 ? (d.gasto / d.planejado) * 100 : 0
    const estourado = d.gasto > d.planejado
    return {
      categoria: d.categoria,
      planejado: d.planejado,
      gasto: d.gasto,
      percentual,
      percentualClamp: Math.min(percentual, 100),
      percentualExcedente: Math.max(percentual - 100, 0),
      estourado,
    }
  })
)
</script>

<template>
  <div class="orc-list">
    <div v-for="(linha, i) in linhas" :key="i" class="orc-row">
      <div class="orc-head">
        <span class="orc-cat">{{ linha.categoria }}</span>
        <span class="orc-pct" :class="{ 'is-over': linha.estourado }">
          {{ Math.round(linha.percentual) }}%
        </span>
      </div>

      <div class="orc-vals" :title="`Gasto ${formatarMoeda(linha.gasto)} de ${formatarMoeda(linha.planejado)}`">
        <span class="orc-gasto" :class="{ 'is-over': linha.estourado }">
          {{ formatarCompacto(linha.gasto) }}
        </span>
        <span class="orc-sep">/</span>
        <span class="orc-plan">{{ formatarCompacto(linha.planejado) }}</span>
      </div>

      <div class="orc-track">
        <div
          class="orc-fill"
          :class="{ 'is-over': linha.estourado }"
          :style="{ width: linha.percentualClamp + '%' }"
        ></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.orc-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.orc-row {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto auto;
  column-gap: 12px;
  row-gap: 4px;
  align-items: baseline;
}

.orc-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.orc-cat {
  font-size: 13px;
  color: var(--ink, #1f1f1c);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.orc-pct {
  font-family: "Geist Mono", monospace;
  font-size: 11px;
  color: var(--ink-3, #82827a);
  font-variant-numeric: tabular-nums;
}

.orc-pct.is-over {
  color: var(--crit, #b53d2c);
  font-weight: 600;
}

.orc-vals {
  grid-column: 2;
  grid-row: 1;
  font-family: "Geist", sans-serif;
  font-size: 12px;
  color: var(--ink-3, #82827a);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.orc-gasto {
  font-weight: 600;
  color: var(--ink, #1f1f1c);
}

.orc-gasto.is-over {
  color: var(--crit, #b53d2c);
}

.orc-sep {
  margin: 0 4px;
  color: var(--ink-3, #82827a);
}

.orc-plan {
  color: var(--ink-3, #82827a);
}

.orc-track {
  grid-column: 1 / -1;
  height: 6px;
  background: var(--paper-2, #e6e6df);
  border-radius: 3px;
  overflow: hidden;
}

.orc-fill {
  height: 100%;
  background: var(--brand, #1F5C3A);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.orc-fill.is-over {
  background: var(--crit, #b53d2c);
}
</style>
