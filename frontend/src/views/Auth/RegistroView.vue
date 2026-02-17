<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { register, loading, error } = useAuth()

const nome = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const role = ref<'user'>('user') // Apenas 'user' por enquanto
const localError = ref('')

const handleRegister = async () => {
  localError.value = ''
  
  if (password.value !== confirmPassword.value) {
    localError.value = 'As senhas não coincidem'
    return
  }
  
  if (password.value.length < 6) {
    localError.value = 'A senha deve ter no mínimo 6 caracteres'
    return
  }

  const success = await register({
    nome: nome.value,
    email: email.value,
    password: password.value,
    role: role.value
  })
  
  if (success) {
    router.push('/login')
  }
}
</script>
<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center py-8">
    <div class="card w-full max-w-md bg-white shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-3xl font-bold text-center mb-6">
          Criar Conta
        </h2>

        <div v-if="error || localError" class="alert alert-error mb-4">
          <span>{{ error || localError }}</span>
        </div>

        <form @submit.prevent="handleRegister">
          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Nome Completo</span>
            </label>
            <input
              v-model="nome"
              type="text"
              placeholder="Seu nome"
              class="input input-bordered"
              required
            />
          </div>

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

          <div class="form-control mb-4">
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

          <div class="form-control mb-4">
            <label class="label">
              <span class="label-text">Confirmar Senha</span>
            </label>
            <input
              v-model="confirmPassword"
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
            <span v-else>Criar Conta</span>
          </button>
        </form>

        <div class="divider">OU</div>

        <RouterLink to="/login" class="btn btn-outline w-full">
          Já tenho uma conta
        </RouterLink>

        <RouterLink to="/" class="btn btn-ghost w-full mt-4">
          Voltar para Home
        </RouterLink>
      </div>
    </div>
  </div>
</template>