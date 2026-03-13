<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Navbar from './components/Navbar.vue'
import Footer from './components/Footer.vue'

const authStore = useAuthStore()
const route = useRoute()

const mostrarNavbar = computed(() => {
  const rotaProtegida = route.matched.some((record) => record.meta.requiresAuth)
  const rotaSemNavbar = route.path === '/'
  return rotaProtegida && !rotaSemNavbar && !!authStore.token
})

const mostrarFooter = computed(() => {
  const rotasSemFooter = ['/login', '/registro']
  return !rotasSemFooter.includes(route.path)
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-base-200">
    <Navbar v-if="mostrarNavbar" />
    <main class="flex-1">
      <router-view />
    </main>
    <Footer v-if="mostrarFooter" />
  </div>
</template>

<style>
html, body {
  @apply bg-base-200;
}
</style>
