<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { Delegacao, DelegacaoContextOption } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const navItems = [
  { rota: 'dashboard', label: 'Dashboard', icon: '📊' },
  { rota: 'transacoes', label: 'Transacoes', icon: '💸' },
  { rota: 'contas', label: 'Contas', icon: '🏦' },
  { rota: 'metas', label: 'Metas', icon: '🎯' },
  { rota: 'orcamentos', label: 'Orcamentos', icon: '🧾' },
  { rota: 'categorias', label: 'Categorias', icon: '🏷️' },
  { rota: 'relatorios', label: 'Relatorios', icon: '🖨️' },
]

const rotaAtiva = computed(() => router.currentRoute.value.name)
const contextOptions = ref<DelegacaoContextOption[]>([])
const selectedContextId = ref<string>('')
const pendingInviteCount = ref(0)

const closeMobileMenu = () => {
  const activeElement = document.activeElement as HTMLElement | null
  activeElement?.blur()
}

const navegarPara = (nomeRota: string) => {
  router.push({ name: nomeRota })
}

const navegarParaMobile = (nomeRota: string) => {
  navegarPara(nomeRota)
  closeMobileMenu()
}

const irParaConvidar = () => {
  router.push({ name: 'delegacoes-convidar' })
}

const irParaConvidarMobile = () => {
  irParaConvidar()
  closeMobileMenu()
}

const irParaConvites = () => {
  router.push({ name: 'delegacoes-convites' })
}

const irParaConvitesMobile = () => {
  irParaConvites()
  closeMobileMenu()
}

const logout = () => {
  authStore.logout()
  localStorage.removeItem('act_as_user_id')
  router.push('/login')
}

const logoutMobile = () => {
  logout()
  closeMobileMenu()
}

const fetchContextOptions = async () => {
  if (!authStore.token) return

  try {
    const response = await api.get('/delegacoes/act-as-options')
    contextOptions.value = response.data

    const stored = localStorage.getItem('act_as_user_id')
    const ownId = String(authStore.user?.id || '')

    if (stored && contextOptions.value.some((opt) => String(opt.user_id) === stored)) {
      selectedContextId.value = stored
      return
    }

    selectedContextId.value = ownId
    localStorage.removeItem('act_as_user_id')
  } catch {
    contextOptions.value = []
  }
}

const fetchPendingInvites = async () => {
  if (!authStore.token) return
  try {
    const response = await api.get('/delegacoes/received')
    pendingInviteCount.value = response.data.filter((item: Delegacao) => item.status === 'pending').length
  } catch {
    pendingInviteCount.value = 0
  }
}

const aplicarContexto = async () => {
  const ownId = String(authStore.user?.id || '')

  if (!selectedContextId.value || selectedContextId.value === ownId) {
    localStorage.removeItem('act_as_user_id')
  } else {
    localStorage.setItem('act_as_user_id', selectedContextId.value)
  }

  router.go(0)
}

onMounted(() => {
  fetchContextOptions()
  fetchPendingInvites()
})
</script>

<template>
  <nav class="navbar bg-primary text-primary-content shadow-lg sticky top-0 z-40">
    <div class="navbar-start">
      <button @click="navegarPara('dashboard')" class="btn btn-ghost text-xl font-bold">
        Financas
      </button>
    </div>

    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal gap-1">
        <li v-for="item in navItems" :key="item.rota">
          <button
            @click="navegarPara(item.rota)"
            :class="[
              'btn btn-sm',
              rotaAtiva === item.rota
                ? 'btn-active btn-secondary'
                : 'btn-ghost'
            ]"
          >
            <span>{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </button>
        </li>
      </ul>
    </div>

    <div class="navbar-end gap-2">
      <div class="hidden lg:flex items-center gap-2">
        <select
          v-if="contextOptions.length > 0"
          v-model="selectedContextId"
          @change="aplicarContexto"
          class="select select-bordered select-sm text-base-content"
        >
          <option v-for="ctx in contextOptions" :key="ctx.user_id" :value="String(ctx.user_id)">
            {{ ctx.nome }}{{ ctx.is_owner ? ' (Meu espaco)' : '' }}
          </option>
        </select>

        <button @click="irParaConvidar" class="btn btn-sm btn-ghost">Convidar</button>
        <button @click="irParaConvites" class="btn btn-sm btn-ghost">
          Convites
          <span v-if="pendingInviteCount" class="badge badge-warning badge-sm">{{ pendingInviteCount }}</span>
        </button>
        <span class="text-sm opacity-75">{{ authStore.user?.nome }}</span>
        <button @click="logout" class="btn btn-sm btn-ghost">Sair</button>
      </div>

      <div class="dropdown dropdown-end lg:hidden">
        <label tabindex="0" class="btn btn-ghost btn-circle">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
          </svg>
        </label>
        <ul tabindex="0" class="dropdown-content menu p-4 shadow bg-base-100 text-base-content rounded-box w-64 z-50">
          <li v-for="item in navItems" :key="item.rota">
            <a @click="navegarParaMobile(item.rota)">
              <span class="mr-2">{{ item.icon }}</span>{{ item.label }}
            </a>
          </li>

          <li v-if="contextOptions.length > 0" class="mt-2">
            <label class="text-xs opacity-60 mb-1">Contexto</label>
            <select
              v-model="selectedContextId"
              @change="aplicarContexto"
              class="select select-bordered w-full"
            >
              <option v-for="ctx in contextOptions" :key="ctx.user_id" :value="String(ctx.user_id)">
                {{ ctx.nome }}{{ ctx.is_owner ? ' (Meu espaco)' : '' }}
              </option>
            </select>
          </li>

          <li>
            <a @click="irParaConvidarMobile">Convidar</a>
          </li>
          <li>
            <a @click="irParaConvitesMobile">
              Convites
              <span v-if="pendingInviteCount" class="badge badge-warning badge-sm ml-2">{{ pendingInviteCount }}</span>
            </a>
          </li>
          <li class="border-t mt-2 pt-2">
            <a @click="logoutMobile" class="text-error">Sair</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

