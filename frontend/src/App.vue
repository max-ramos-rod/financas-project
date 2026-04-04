<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import Navbar from './components/Navbar.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const route = useRoute()

authStore.initializeSessionMonitoring()

const mostrarNavbar = computed(() => {
  const rotaProtegida = route.matched.some((record) => record.meta.requiresAuth)
  const rotaSemNavbar = route.path === '/'
  return rotaProtegida && !rotaSemNavbar && !!authStore.token
})
</script>

<template>
  <div>
    <Navbar v-if="mostrarNavbar" />
    <router-view />
  </div>
</template>

<style>
html, body {
  @apply bg-base-200;
}
</style>
