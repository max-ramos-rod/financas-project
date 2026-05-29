<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import Lockup from '@/components/layout/Lockup.vue'
import { extractApiError } from '@/services/apiError'

const router = useRouter()
const email = ref('')
const loading = ref(false)
const error = ref('')
const enviado = ref(false)

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  try {
    await api.post('/auth/forgot-password', { email: email.value })
    enviado.value = true
  } catch (err) {
    error.value = extractApiError(err, 'Erro ao processar solicitação.')
  } finally {
    loading.value = false
  }
}
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
            Recupere o<br>
            acesso à sua <span class="text-primary">conta</span>.
          </h2>

          <p class="mt-5 text-base leading-relaxed text-base-content/70 max-w-[38ch]">
            Informe seu e-mail e enviaremos as instruções para você criar uma nova senha com segurança.
          </p>
        </div>

        <!-- Direita: card -->
        <div class="w-full max-w-md mx-auto lg:mx-0 lg:ml-auto">
          <div class="card bg-base-100 border border-base-300 shadow-lg">
            <div class="card-body gap-0 p-8 lg:p-9">

              <template v-if="!enviado">
                <h3 class="text-2xl font-semibold tracking-tight mb-1">Esqueci a senha</h3>
                <p class="text-sm text-base-content/50 mb-7">Enviaremos um link de recuperação para seu e-mail.</p>

                <div v-if="error" class="alert alert-error mb-5">
                  <span>{{ error }}</span>
                </div>

                <form @submit.prevent="handleSubmit" class="space-y-5">
                  <div class="form-control">
                    <label class="label py-0 pb-1.5">
                      <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/60">E-mail</span>
                    </label>
                    <input
                      v-model="email"
                      type="email"
                      placeholder="você@email.com"
                      class="input input-bordered w-full"
                      required
                      autocomplete="email"
                    />
                  </div>

                  <button
                    type="submit"
                    class="btn btn-primary w-full mt-1"
                    :disabled="loading"
                  >
                    <span v-if="loading" class="loading loading-spinner loading-sm"></span>
                    <span v-else>Enviar instruções</span>
                  </button>
                </form>

                <p class="mt-6 text-center text-xs text-base-content/40">
                  Lembrou a senha?
                  <router-link to="/login" class="text-primary font-medium hover:underline">Voltar para login</router-link>
                </p>
              </template>

              <template v-else>
                <h3 class="text-2xl font-semibold tracking-tight mb-1">Verifique seu e-mail</h3>

                <div class="alert alert-success mb-5 mt-4">
                  <span>Enviamos as instruções de recuperação para <strong>{{ email }}</strong>. Verifique sua caixa de entrada.</span>
                </div>

                <button
                  class="btn btn-primary w-full mt-1"
                  @click="router.push('/login')"
                >
                  Voltar para login
                </button>
              </template>

            </div>
          </div>
        </div>

      </div>
    </main>

    <!-- Footer inline -->
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
