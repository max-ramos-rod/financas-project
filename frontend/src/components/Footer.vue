<script setup lang="ts">
const anoAtual = new Date().getFullYear()
</script>

<template>
  <footer class="footer footer-center border-t border-base-300 bg-base-100 px-6 py-4 text-base-content">
    <aside class="space-y-1">
      <p class="text-sm font-semibold">Financas</p>
      <p class="text-xs opacity-70">Gestao financeira com foco em clareza e controle.</p>
      <p class="text-xs opacity-50">(c) {{ anoAtual }} Financas. Todos os direitos reservados.</p>
    </aside>
  </footer>
</template>
