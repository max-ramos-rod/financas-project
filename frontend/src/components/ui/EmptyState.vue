<script setup lang="ts">
/**
 * EmptyState · Estado vazio reutilizável
 *
 * Variantes:
 *   - first-time  · primeira vez, ainda não há dados (verde · convidativo)
 *   - filtered    · filtros não retornaram resultado (cinza · neutro)
 *   - error       · erro de carregamento (vermelho · ação corretiva)
 *   - zero-state  · sem dados no período/contexto atual (verde · onboarding)
 *
 * Uso:
 *   <EmptyState variant="first-time" title="Ainda nada." description="...">
 *     <template #icon><ListIcon /></template>
 *     <template #actions><button class="btn btn-primary btn-sm">Lançar</button></template>
 *   </EmptyState>
 */

interface Props {
  variant?: 'first-time' | 'filtered' | 'error' | 'zero-state'
  title: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  variant: 'first-time',
})
</script>

<template>
  <div class="empty" :class="`is-${variant}`">
    <div class="empty-icon">
      <slot name="icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 7h16M4 12h10M4 17h6" />
        </svg>
      </slot>
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-desc">{{ description }}</p>
    <div v-if="$slots.actions" class="empty-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.empty {
  text-align: center;
  max-width: 360px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 16px;
}

.empty-icon {
  width: 96px;
  height: 96px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--r-xl, 14px);
}

.empty-icon :deep(svg) {
  width: 48px;
  height: 48px;
}

.empty.is-first-time .empty-icon,
.empty.is-zero-state .empty-icon {
  background: var(--brand-tint);
  color: var(--brand);
}

.empty.is-filtered .empty-icon {
  background: var(--paper-2);
  color: var(--ink-3);
}

.empty.is-error .empty-icon {
  background: var(--crit-tint);
  color: var(--crit);
}

.empty-title {
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: 20px;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 0;
}

.empty-desc {
  font-size: 14px;
  line-height: 1.5;
  color: var(--ink-2);
  margin: 4px 0 0;
  max-width: 36ch;
}

.empty-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
