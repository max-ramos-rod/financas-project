<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, loading, error } = useAuth()

const email = ref('')
const password = ref('')

const getDashboardRoute = (role: string): string => {
  const routes: Record<string, string> = {
    user: '/dashboard'
  }
  return routes[role] || '/dashboard'
}


const handleLogin = async () => {
  const success = await login({
    email: email.value,
    password: password.value
  })
  
  if (success) {
    const { user } = useAuth()
    router.push(getDashboardRoute(user.value?.role || 'user'))
  }
}
</script>

<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center">
    <div class="card w-full max-w-md bg-white shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-3xl font-bold text-center mb-6">
          Login
        </h2>

        <div v-if="error" class="alert alert-error mb-4">
          <span>{{ error }}</span>
        </div>

        <form @submit.prevent="handleLogin">
          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Email</span>
            </label>
            <input
              v-model="email"
              type="email"
              placeholder="seu@email.com"
              class="input input-bordered"
              required
            />
          </div>

          <div class="form-control mb-6">
            <label class="label">
              <span class="label-text">Senha</span>
            </label>
            <input
              v-model="password"
              type="password"
              placeholder="••••••••"
              class="input input-bordered"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary w-full"
            :disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner"></span>
            <span v-else>Entrar</span>
          </button>
        </form>

        <div class="divider">OU</div>

        <RouterLink to="/registro" class="btn btn-outline w-full">
          Criar uma conta
        </RouterLink>

        <RouterLink to="/" class="btn btn-ghost w-full mt-4">
          Voltar para Home
        </RouterLink>
      </div>
    </div>
  </div>
</template>
