#!/bin/bash
cd "$(dirname "$0")/frontend"

# main.ts
cat > src/main.ts << 'EOF'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/style.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
EOF

# style.css
cat > src/assets/style.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

# App.vue
cat > src/App.vue << 'EOF'
<template>
  <RouterView />
</template>

<script setup lang="ts">
// App raiz
</script>
EOF

# router
cat > src/router/index.ts << 'EOF'
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Auth/LoginView.vue')
    },
    {
      path: '/registro',
      name: 'registro',
      component: () => import('@/views/Auth/RegistroView.vue')
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/Dashboard/IndexView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/transacoes',
      name: 'transacoes',
      component: () => import('@/views/Transacoes/ListaView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

export default router
EOF

mkdir -p src/router
cat > src/router/index.ts << 'EOF'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { requiresAuth: true } }
  ]
})

export default router
EOF

# types
cat > src/types/index.ts << 'EOF'
export interface User {
  id: number
  email: string
  nome: string
  role: string
}

export interface Conta {
  id: number
  nome: string
  tipo: string
  saldo: number
  cor: string
  ativa: boolean
}

export interface Categoria {
  id: number
  nome: string
  icone: string
  cor: string
  tipo: string
  padrao: boolean
}

export interface Transacao {
  id: number
  conta_id: number
  categoria_id: number
  descricao: string
  valor: number
  tipo: "entrada" | "saida" | "transferencia"
  data: string
  fixa: boolean
  tem_dizimo: boolean
  percentual_dizimo: number
  e_dizimo: boolean
  parcelado: boolean
  parcela_atual?: number
  total_parcelas?: number
}

export interface Meta {
  id: number
  nome: string
  valor_alvo: number
  valor_atual: number
  data_inicio: string
  data_fim?: string
  concluida: boolean
}
EOF

# services
cat > src/services/api.ts << 'EOF'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
EOF

# stores
cat > src/stores/auth.ts << 'EOF'
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('username', email)
      formData.append('password', password)
      const response = await api.post('/auth/login', formData)
      token.value = response.data.access_token
      localStorage.setItem('access_token', response.data.access_token)
      await fetchUser()
      return true
    } catch (error) {
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    const response = await api.get('/auth/me')
    user.value = response.data
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
  }

  return { user, token, loading, login, logout, fetchUser }
})
EOF

# views
mkdir -p src/views/Auth src/views/Dashboard src/views/Transacoes

cat > src/views/HomeView.vue << 'EOF'
<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-5xl font-bold mb-4">💰 Finanças Cristãs</h1>
      <p class="text-xl mb-8">Controle suas finanças com sabedoria</p>
      <div class="space-x-4">
        <router-link to="/login" class="btn btn-primary">Entrar</router-link>
        <router-link to="/registro" class="btn btn-outline">Criar Conta</router-link>
      </div>
    </div>
  </div>
</template>
EOF

cat > src/views/LoginView.vue << 'EOF'
<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center">
    <div class="card w-96 bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title">Login</h2>
        <input type="email" placeholder="Email" class="input input-bordered" />
        <input type="password" placeholder="Senha" class="input input-bordered" />
        <button class="btn btn-primary">Entrar</button>
      </div>
    </div>
  </div>
</template>
EOF

cat > src/views/DashboardView.vue << 'EOF'
<template>
  <div class="min-h-screen bg-base-200 p-4">
    <h1 class="text-3xl font-bold mb-4">Dashboard</h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Saldo Total</h2>
          <p class="text-3xl font-bold text-success">R$ 0,00</p>
        </div>
      </div>
    </div>
  </div>
</template>
EOF

echo "✅ Arquivos frontend criados!"
ls -R src/

