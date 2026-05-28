<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Lockup from '@/components/Lockup.vue'

const router = useRouter()
const authStore = useAuthStore()
const { loading, error } = storeToRefs(authStore)
const { register } = authStore

const nome = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirm = ref(false)
const localError = ref('')

const passwordStrength = computed(() => {
  const p = password.value
  if (p.length === 0) return null
  if (p.length < 6) return { label: 'curta demais', tone: 'text-error' }
  if (p.length < 10) return { label: 'razoável', tone: 'text-warning' }
  return { label: 'boa', tone: 'text-success' }
})

const handleRegister = async () => {
  localError.value = ''

  if (password.value !== confirmPassword.value) {
    localError.value = 'As senhas não coincidem.'
    return
  }

  if (password.value.length < 6) {
    localError.value = 'A senha precisa ter no mínimo 6 caracteres.'
    return
  }

  const success = await register({
    nome: nome.value,
    email: email.value,
    password: password.value,
    role: 'user'
  })

  if (success) {
    router.push('/login')
  }
}
</script>

<template>
  <div class="flex flex-col min-h-screen">

    <!-- Header público -->
    <header class="bg-base-100 border-b border-base-300 h-16 flex items-center px-6 lg:px-8 shrink-0">
      <Lockup size="sm" to="/" />
      <div class="flex-1"></div>
      <router-link to="/" class="text-sm text-base-content/60 hover:text-base-content transition-colors">
        Voltar pra Home
      </router-link>
    </header>

    <!-- Conteúdo principal -->
    <main class="flex-1 flex items-center">
      <div class="container mx-auto px-6 lg:px-8 py-16 grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-20 items-center" style="min-height: 520px">

        <!-- Esquerda: pitch -->
        <div>
          <div class="mb-10">
            <Lockup size="md" />
          </div>

          <h2 class="text-[clamp(28px,3vw,44px)] font-semibold leading-[1.05] tracking-[-0.025em]">
            Comece com o seu <span class="text-primary">primeiro mês</span>.<br>
            Sem cartão, sem mágica.
          </h2>

          <p class="mt-5 text-base leading-relaxed text-base-content/60 max-w-[38ch]">
            Você cria sua conta, lança o que ganha e o que gasta, e o mês fica claro. É só isso.
          </p>

          <ul class="mt-8 space-y-3 text-sm text-base-content/70 max-w-[40ch]">
            <li class="flex items-start gap-3">
              <span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-primary shrink-0"></span>
              <span>Grátis pra começar — sem trial, sem pegadinha.</span>
            </li>
            <li class="flex items-start gap-3">
              <span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-primary shrink-0"></span>
              <span>Seus dados ficam no seu espaço, criptografados.</span>
            </li>
            <li class="flex items-start gap-3">
              <span class="mt-[7px] w-1.5 h-1.5 rounded-full bg-primary shrink-0"></span>
              <span>Convide quem participa do orçamento — cônjuge, contador.</span>
            </li>
          </ul>
        </div>

        <!-- Direita: card de registro -->
        <div class="w-full max-w-md mx-auto lg:mx-0 lg:ml-auto">
          <div class="card bg-base-100 border border-base-300 shadow-lg">
            <div class="card-body gap-0 p-8 lg:p-9">

              <h3 class="text-2xl font-semibold tracking-tight mb-1">Criar conta</h3>
              <p class="text-sm text-base-content/50 mb-7">Leva menos de um minuto.</p>

              <div v-if="error || localError" class="alert alert-error mb-5">
                <span>{{ error || localError }}</span>
              </div>

              <form @submit.prevent="handleRegister" class="space-y-5">

                <div class="form-control">
                  <label class="label py-0 pb-1.5">
                    <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Nome</span>
                  </label>
                  <input
                    v-model="nome"
                    type="text"
                    placeholder="Como você quer ser chamado"
                    class="input input-bordered"
                    required
                    autocomplete="name"
                  />
                </div>

                <div class="form-control">
                  <label class="label py-0 pb-1.5">
                    <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">E-mail</span>
                  </label>
                  <input
                    v-model="email"
                    type="email"
                    placeholder="você@email.com"
                    class="input input-bordered"
                    required
                    autocomplete="email"
                  />
                </div>

                <div class="form-control">
                  <label class="label py-0 pb-1.5 flex justify-between items-center">
                    <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Senha</span>
                    <span
                      v-if="passwordStrength"
                      class="text-[11px] font-mono uppercase tracking-widest"
                      :class="passwordStrength.tone"
                    >
                      {{ passwordStrength.label }}
                    </span>
                  </label>
                  <div class="relative">
                    <input
                      v-model="password"
                      :type="showPassword ? 'text' : 'password'"
                      placeholder="Mínimo 6 caracteres"
                      class="input input-bordered w-full pr-20"
                      required
                      autocomplete="new-password"
                    />
                    <button
                      type="button"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-mono text-base-content/40 hover:text-base-content transition-colors"
                      @click="showPassword = !showPassword"
                    >
                      {{ showPassword ? 'ocultar' : 'mostrar' }}
                    </button>
                  </div>
                </div>

                <div class="form-control">
                  <label class="label py-0 pb-1.5">
                    <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/50">Confirmar senha</span>
                  </label>
                  <div class="relative">
                    <input
                      v-model="confirmPassword"
                      :type="showConfirm ? 'text' : 'password'"
                      placeholder="Repita a senha"
                      class="input input-bordered w-full pr-20"
                      required
                      autocomplete="new-password"
                    />
                    <button
                      type="button"
                      class="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-mono text-base-content/40 hover:text-base-content transition-colors"
                      @click="showConfirm = !showConfirm"
                    >
                      {{ showConfirm ? 'ocultar' : 'mostrar' }}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  class="btn btn-primary w-full mt-1"
                  :disabled="loading"
                >
                  <span v-if="loading" class="loading loading-spinner loading-sm"></span>
                  <span v-else>Criar conta</span>
                </button>

              </form>

              <p class="mt-6 text-center text-xs text-base-content/40">
                Já tem conta?
                <router-link to="/login" class="text-primary font-medium hover:underline">Entrar</router-link>
              </p>

            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Footer inline (App.vue exclui /registro do footer global, se aplicável) -->
    <footer class="bg-base-100 border-t border-base-300 px-6 lg:px-8 py-6 shrink-0">
      <div class="container mx-auto flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex items-center gap-3 text-sm text-base-content/40">
          <Lockup size="sm" />
          <span>· gestão financeira com foco em clareza e controle</span>
        </div>
        <div class="flex gap-5 text-xs text-base-content/40">
          <a href="#" class="hover:text-base-content transition-colors">Sobre</a>
          <a href="#" class="hover:text-base-content transition-colors">Ajuda</a>
          <a href="#" class="hover:text-base-content transition-colors">Termos</a>
          <span>© {{ new Date().getFullYear() }}</span>
        </div>
      </div>
    </footer>

  </div>
</template>