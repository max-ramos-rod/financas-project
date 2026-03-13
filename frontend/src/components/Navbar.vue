<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import type { Delegacao, DelegacaoContextOption } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

type NavIconKey = 'dashboard' | 'transacoes' | 'contas' | 'metas' | 'orcamentos' | 'categorias' | 'relatorios'

const navItems: Array<{ rota: string; label: string; icon: NavIconKey }> = [
  { rota: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { rota: 'transacoes', label: 'Transacoes', icon: 'transacoes' },
  { rota: 'contas', label: 'Contas', icon: 'contas' },
  { rota: 'metas', label: 'Metas', icon: 'metas' },
  { rota: 'orcamentos', label: 'Orcamentos', icon: 'orcamentos' },
  { rota: 'categorias', label: 'Categorias', icon: 'categorias' },
  { rota: 'relatorios', label: 'Relatorios', icon: 'relatorios' },
]

const iconPaths: Record<NavIconKey, string> = {
  dashboard: 'M3 13.5 12 3l9 10.5V21a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-7.5Z',
  transacoes: 'M17 9V5l4 4-4 4V9H7a4 4 0 1 0 4 4h2a6 6 0 1 1-6-6h10Zm-10 6v4l-4-4 4-4v4h10a4 4 0 1 0-4-4h-2a6 6 0 1 1 6 6H7Z',
  contas: 'M3 7.5 12 3l9 4.5v2H3v-2Zm2 4h2v6H5v-6Zm6 0h2v6h-2v-6Zm6 0h2v6h-2v-6ZM3 20h18v2H3v-2Z',
  metas: 'M12 3a9 9 0 1 0 9 9 9 9 0 0 0-9-9Zm0 2a7 7 0 0 1 6.71 5h-2.17A5 5 0 0 0 12 7Zm0 14a7 7 0 0 1-6.71-5h2.17A5 5 0 0 0 12 17Zm1-8 4.5-4.5 1.5 1.5L14.5 12.5 13 11Z',
  orcamentos: 'M4 6h16v3H4V6Zm0 5h10v3H4v-3Zm0 5h16v3H4v-3Z',
  categorias: 'M4 7h7l2 2h7v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7Z',
  relatorios: 'M6 3h9l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Zm8 1.5V9h4.5L14 4.5ZM8 13h8v1.5H8V13Zm0 4h8v1.5H8V17Z',
}

const navItemsPrincipais = navItems.filter((item) => ['dashboard', 'transacoes', 'contas'].includes(item.rota))
const navItemsGestao = navItems.filter((item) => ['metas', 'orcamentos', 'categorias', 'relatorios'].includes(item.rota))

const rotaAtiva = computed(() => router.currentRoute.value.name)
const contextOptions = ref<DelegacaoContextOption[]>([])
const selectedContextId = ref<string>('')
const pendingInviteCount = ref(0)

const closeMobileMenu = () => {
  const activeElement = document.activeElement as HTMLElement | null
  activeElement?.blur()
}

const isRotaAtiva = (rotas: string[]) => rotas.includes(String(rotaAtiva.value || ''))

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
      <ul class="menu menu-horizontal items-center gap-1 rounded-box bg-primary/10 px-2 py-1">
        <li v-for="item in navItemsPrincipais" :key="item.rota">
          <button
            @click="navegarPara(item.rota)"
            :class="[
              'btn btn-sm',
              rotaAtiva === item.rota
                ? 'btn-active btn-secondary'
                : 'btn-ghost'
            ]"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path :d="iconPaths[item.icon]" />
            </svg>
            <span>{{ item.label }}</span>
          </button>
        </li>
        <li>
          <details>
            <summary
              :class="[
                'btn btn-sm list-none',
                isRotaAtiva(navItemsGestao.map((item) => item.rota))
                  ? 'btn-active btn-secondary'
                  : 'btn-ghost'
              ]"
            >
              <span>Gestao</span>
            </summary>
            <ul class="bg-base-100 text-base-content rounded-box z-50 mt-3 w-56 p-2 shadow-lg">
              <li v-for="item in navItemsGestao" :key="item.rota">
                <a @click="navegarPara(item.rota)" :class="{ 'menu-active': rotaAtiva === item.rota }">
                  <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path :d="iconPaths[item.icon]" />
                  </svg>
                  <span>{{ item.label }}</span>
                </a>
              </li>
            </ul>
          </details>
        </li>
      </ul>
    </div>

    <div class="navbar-end gap-2">
      <div class="hidden lg:flex items-center gap-2">
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-sm btn-ghost">
            Colaboracao
            <span v-if="pendingInviteCount" class="badge badge-warning badge-sm">{{ pendingInviteCount }}</span>
          </div>
          <ul tabindex="0" class="dropdown-content menu bg-base-100 text-base-content rounded-box z-50 mt-3 w-60 p-2 shadow-lg">
            <li>
              <a @click="irParaConvidar">
                <span>Convidar</span>
              </a>
            </li>
            <li>
              <a @click="irParaConvites" class="flex items-center justify-between">
                <span>Convites</span>
                <span v-if="pendingInviteCount" class="badge badge-warning badge-sm">{{ pendingInviteCount }}</span>
              </a>
            </li>
          </ul>
        </div>

        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-sm btn-ghost">
            {{ authStore.user?.nome || 'Usuario' }}
          </div>
          <div tabindex="0" class="dropdown-content rounded-box bg-base-100 text-base-content z-50 mt-3 w-72 p-3 shadow-lg">
            <div class="space-y-3">
              <div class="text-xs font-semibold uppercase tracking-wide opacity-60">Conta</div>
              <div class="text-sm font-medium">{{ authStore.user?.nome }}</div>
              <div v-if="contextOptions.length > 0" class="space-y-1">
                <label class="text-xs opacity-60">Contexto</label>
                <select
                  v-model="selectedContextId"
                  @change="aplicarContexto"
                  class="select select-bordered select-sm w-full text-base-content"
                >
                  <option v-for="ctx in contextOptions" :key="ctx.user_id" :value="String(ctx.user_id)">
                    {{ ctx.nome }}{{ ctx.is_owner ? ' (Meu espaco)' : '' }}
                  </option>
                </select>
              </div>
              <button @click="logout" class="btn btn-sm btn-outline btn-error w-full">Sair</button>
            </div>
          </div>
        </div>
      </div>

      <div class="dropdown dropdown-end lg:hidden">
        <label tabindex="0" class="btn btn-ghost btn-circle">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
          </svg>
        </label>
        <ul tabindex="0" class="dropdown-content menu p-4 shadow bg-base-100 text-base-content rounded-box w-72 z-50">
          <li class="menu-title"><span>Navegacao</span></li>
          <li v-for="item in navItemsPrincipais" :key="item.rota">
            <a @click="navegarParaMobile(item.rota)">
              <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path :d="iconPaths[item.icon]" />
              </svg>
              {{ item.label }}
            </a>
          </li>
          <li class="menu-title mt-2"><span>Gestao</span></li>
          <li v-for="item in navItemsGestao" :key="`mobile-${item.rota}`">
            <a @click="navegarParaMobile(item.rota)">
              <svg class="mr-2 h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path :d="iconPaths[item.icon]" />
              </svg>
              {{ item.label }}
            </a>
          </li>
          <li class="menu-title mt-2"><span>Colaboracao</span></li>
          <li>
            <a @click="irParaConvidarMobile">Convidar</a>
          </li>
          <li>
            <a @click="irParaConvitesMobile" class="flex items-center justify-between">
              <span>Convites</span>
              <span v-if="pendingInviteCount" class="badge badge-warning badge-sm ml-2">{{ pendingInviteCount }}</span>
            </a>
          </li>
          <li v-if="contextOptions.length > 0" class="menu-title mt-2"><span>Conta</span></li>
          <li v-if="contextOptions.length > 0" class="px-2 py-1">
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
          <li class="border-t mt-2 pt-2">
            <a @click="logoutMobile" class="text-error">Sair</a>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

