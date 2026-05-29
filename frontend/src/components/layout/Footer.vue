<script setup lang="ts">
import Lockup from './Lockup.vue'

const anoAtual = new Date().getFullYear()
</script>

<template>
  <footer class="footer footer-center border-t border-base-300 bg-base-100 px-6 py-4 text-base-content">
    <aside class="space-y-1">
      <Lockup size="sm" />
      <p class="text-xs opacity-70">Gestão financeira com foco em clareza e controle.</p>
      <p class="text-xs opacity-50">© {{ anoAtual }} Finanças Cristãs. Todos os direitos reservados.</p>
    </aside>
  </footer>
</template>
