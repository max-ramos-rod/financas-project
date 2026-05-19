<script setup lang="ts">
/**
 * Lockup · Marca + texto
 * ----------------------------------------------------------------------------
 * Aplicação completa da marca: F mark + "Finanças Cristãs" em Geist 600.
 * Usado no Navbar, Footer, Home, Login, e em assinatura de e-mail.
 *
 * Uso:
 *   <Lockup size="sm" />                ← navbar, footer (16px texto, 26px mark)
 *   <Lockup size="md" />                ← lockup secundário (22px texto, 32px mark)
 *   <Lockup size="lg" />                ← Home hero (32px texto, 48px mark)
 *   <Lockup to="/dashboard" />          ← vira router-link clicável
 *   <Lockup inverted />                 ← branco sobre fundo escuro (navbar primary)
 */

import BrandMark from './BrandMark.vue'

interface Props {
  size?: 'sm' | 'md' | 'lg'
  to?: string
  inverted?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  inverted: false,
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
    :class="{ 'is-inverted': inverted }"
    :style="{ gap: s.gap, fontSize: s.text }"
  >
    <BrandMark :size="s.mark" :inverted="inverted" />
    <span>Finanças Cristãs</span>
  </router-link>

  <span
    v-else
    class="lockup"
    :class="{ 'is-inverted': inverted }"
    :style="{ gap: s.gap, fontSize: s.text }"
  >
    <BrandMark :size="s.mark" :inverted="inverted" />
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

/* Inverso: texto branco para uso sobre fundo escuro (navbar primary, hero dark) */
.lockup.is-inverted {
  color: #ffffff;
}

.lockup :deep(svg) {
  flex-shrink: 0;
}
</style>