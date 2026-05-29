<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import Lockup from '@/components/layout/Lockup.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const mensagemSucesso = computed(() => route.query.mensagem === 'senha_redefinida' ? 'Senha redefinida com sucesso. Faça login.' : '')
const { login } = authStore
const { loading, error } = storeToRefs(authStore)

const email = ref('')
const password = ref('')
const showPassword = ref(false)

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

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
    router.push(getDashboardRoute(authStore.user?.role || 'user'))
  }
}

const handleGoogleCallback = async (response: { credential: string }) => {
  if (!response?.credential) return
  const success = await authStore.loginWithGoogle(response.credential)
  if (success) {
    router.push(getDashboardRoute(authStore.user?.role || 'user'))
  }
}

onMounted(() => {
  if (!GOOGLE_CLIENT_ID) return
  const g = (window as any).google
  if (!g?.accounts?.id) return
  g.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: handleGoogleCallback })
  const btnEl = document.getElementById('google-btn')
  if (btnEl) {
    g.accounts.id.renderButton(btnEl, { theme: 'outline', size: 'large', width: btnEl.offsetWidth || 320, locale: 'pt-BR' })
  }
})
</script>

<template>
  <div class="flex flex-col min-h-screen">

    <!-- Header público -->
    <header class="bg-base-100 border-b border-base-300 h-16 flex items-center px-6 lg:px-8 shrink-0">
      <Lockup size="sm" to="/" />
      <div class="flex-1"></div>
      <router-link to="/" class="text-sm text-base-content/70 hover:text-base-content transition-colors">
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
            Bem-vindo de volta.<br>
            Vamos olhar o seu <span class="text-primary">mês</span>?
          </h2>

          <p class="mt-5 text-base leading-relaxed text-base-content/70 max-w-[38ch]">
            Seu dashboard, suas contas, suas metas — exatamente como você deixou da última vez.
          </p>
        </div>

        <!-- Direita: card de login -->
        <div class="w-full max-w-md mx-auto lg:mx-0 lg:ml-auto">
          <div class="card bg-base-100 border border-base-300 shadow-lg">
            <div class="card-body gap-0 p-8 lg:p-9">

              <h3 class="text-2xl font-semibold tracking-tight mb-1">Entrar</h3>
              <p class="text-sm text-base-content/50 mb-7">Acesse com seu e-mail e senha.</p>

              <div v-if="mensagemSucesso" class="alert alert-success mb-5"><span>{{ mensagemSucesso }}</span></div>

              <div v-if="error" class="alert alert-error mb-5">
                <span>{{ error }}</span>
              </div>

              <form @submit.prevent="handleLogin" class="space-y-5">

                <div class="form-control">
                  <label class="label py-0 pb-1.5">
                    <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/60">E-mail</span>
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
                  <label class="label py-0 pb-1.5">
                    <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/60">Senha</span>
                  </label>
                  <div class="relative">
                    <input
                      v-model="password"
                      :type="showPassword ? 'text' : 'password'"
                      placeholder="••••••••"
                      class="input input-bordered w-full pr-20"
                      required
                      autocomplete="current-password"
                    />
                    <button
                      type="button"
                      class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center justify-center min-w-[44px] min-h-[44px] text-[11px] font-mono text-base-content/60 hover:text-base-content transition-colors"
                      @click="showPassword = !showPassword"
                    >
                      {{ showPassword ? 'ocultar' : 'mostrar' }}
                    </button>
                  </div>
                </div>

                <div class="flex items-center justify-between text-sm">
                  <label class="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" class="checkbox checkbox-sm" />
                    <span class="text-base-content/70">Continuar conectado</span>
                  </label>
                  <router-link to="/recuperar-senha" class="text-primary font-medium hover:underline">Esqueci a senha</router-link>
                </div>

                <button
                  type="submit"
                  class="btn btn-primary w-full mt-1"
                  :disabled="loading"
                >
                  <span v-if="loading" class="loading loading-spinner loading-sm"></span>
                  <span v-else>Entrar</span>
                </button>

              </form>

              <template v-if="GOOGLE_CLIENT_ID">
                <div class="divider text-xs text-base-content/30 my-3">ou</div>
                <div id="google-btn" class="flex justify-center"></div>
              </template>

              <p class="mt-6 text-center text-xs text-base-content/40">
                Ainda não tem conta?
                <router-link to="/registro" class="text-primary font-medium hover:underline">Criar conta</router-link>
              </p>

            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Footer inline (App.vue exclui /login do footer global) -->
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
