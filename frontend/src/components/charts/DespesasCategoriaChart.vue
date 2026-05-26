<script setup lang="ts">
/**
 * DespesasCategoriaChart · Versão HTML/CSS pura
 * ----------------------------------------------------------------------------
 * Lista de categorias com barra horizontal proporcional + valor à direita.
 * Não usa ApexCharts — implementação direta em HTML+CSS é mais leve,
 * 100% estável, e segue o mesmo padrão visual do mockup do handoff.
 */

import { computed } from 'vue'

const props = defineProps<{
  dados: { nome: string; valor: number }[]
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

const valorMaximo = computed(() => {
  if (props.dados.length === 0) return 1
  return Math.max(...props.dados.map(d => d.valor), 1)
})

const totalGeral = computed(() =>
  props.dados.reduce((sum, d) => sum + d.valor, 0)
)

const linhas = computed(() =>
  props.dados.map(d => ({
    nome: d.nome,
    valor: d.valor,
    percentual: totalGeral.value > 0 ? Math.round((d.valor / totalGeral.value) * 100) : 0,
    largura: (d.valor / valorMaximo.value) * 100,
  }))
)
</script>

<template>
  <div class="cat-list">
    <div v-for="(linha, i) in linhas" :key="i" class="cat-row">
      <div class="cat-meta">
        <span class="cat-nome">{{ linha.nome }}</span>
        <span class="cat-pct">{{ linha.percentual }}%</span>
      </div>
      <div class="cat-valor">{{ formatarCompacto(linha.valor) }}</div>
      <div class="cat-bar" :title="formatarMoeda(linha.valor)">
        <div class="cat-fill" :style="{ width: linha.largura + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cat-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.cat-row {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  column-gap: 12px;
  row-gap: 6px;
  align-items: baseline;
}

.cat-meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  min-width: 0;
}

.cat-nome {
  font-size: 13px;
  color: var(--ink, #1f1f1c);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cat-pct {
  font-family: "Geist Mono", monospace;
  font-size: 11px;
  color: var(--ink-3, #82827a);
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
}

.cat-valor {
  font-family: "Geist", sans-serif;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink, #1f1f1c);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cat-bar {
  grid-column: 1 / -1;
  height: 4px;
  background: var(--paper-2, #e6e6df);
  border-radius: 2px;
  overflow: hidden;
}

.cat-fill {
  height: 100%;
  background: var(--crit, #b53d2c);
  border-radius: 2px;
  transition: width 0.25s ease;
}
</style>
