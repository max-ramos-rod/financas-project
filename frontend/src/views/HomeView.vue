<script setup lang="ts">
import Lockup from '@/components/Lockup.vue'
</script>

<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center">
    <div class="text-center">
      <div class="flex justify-center mb-6">
        <Lockup size="lg" />
      </div>
      <p class="text-xl mb-8">Controle suas finanças com sabedoria</p>
      <div class="space-x-4">
        <router-link to="/login" class="btn btn-primary">Entrar</router-link>
        <router-link to="/registro" class="btn btn-outline">Criar Conta</router-link>
      </div>
    </div>
  </div>
</template>
