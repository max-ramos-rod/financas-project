<script setup lang="ts">
import BrandMark from './BrandMark.vue'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  to?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const sizeMap = {
  sm: { mark: 26, text: '16px', gap: '12px' },
  md: { mark: 32, text: '22px', gap: '14px' },
  lg: { mark: 48, text: '32px', gap: '16px' },
}

const s = sizeMap[props.size]
</script>

<template>
  <router-link
    v-if="to"
    :to="to"
    class="lockup"
    :style="{ gap: s.gap, fontSize: s.text }"
  >
    <BrandMark :size="s.mark" />
    <span>Finanças Cristãs</span>
  </router-link>

  <span
    v-else
    class="lockup"
    :style="{ gap: s.gap, fontSize: s.text }"
  >
    <BrandMark :size="s.mark" />
    <span>Finanças Cristãs</span>
  </span>
</template>

<style scoped>
.lockup {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-sans);
  font-weight: 600;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--ink);
  text-decoration: none;
}

.lockup :deep(svg) {
  flex-shrink: 0;
}
</style>
