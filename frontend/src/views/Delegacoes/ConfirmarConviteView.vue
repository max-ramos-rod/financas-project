<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import type { DelegacaoInviteTokenInfo } from '@/types'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const confirming = ref(false)
const error = ref('')
const success = ref('')
const info = ref<DelegacaoInviteTokenInfo | null>(null)

const nome = ref('')
const password = ref('')
const confirmPassword = ref('')

const token = computed(() => String(route.query.token || ''))

const carregarInfo = async () => {
  loading.value = true
  error.value = ''
  try {
    if (!token.value) {
      error.value = 'Token de convite ausente.'
      return
    }

    const response = await api.get<DelegacaoInviteTokenInfo>(`/delegacoes/invite-info/${token.value}`)
    info.value = response.data
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Convite invalido.'
  } finally {
    loading.value = false
  }
}

const confirmar = async () => {
  if (!info.value || info.value.expired) return
  error.value = ''
  success.value = ''

  if (!info.value.has_account) {
    if (!nome.value.trim()) {
      error.value = 'Informe seu nome para concluir o cadastro.'
      return
    }
    if (password.value.length < 6) {
      error.value = 'A senha deve ter no minimo 6 caracteres.'
      return
    }
    if (password.value !== confirmPassword.value) {
      error.value = 'As senhas nao coincidem.'
      return
    }
  }

  confirming.value = true
  try {
    await api.post(`/delegacoes/confirm/${token.value}`, {
      nome: info.value.has_account ? null : nome.value.trim(),
      password: info.value.has_account ? null : password.value,
    })
    success.value = 'Convite confirmado com sucesso. Agora faca login para acessar.'
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Falha ao confirmar convite.'
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  carregarInfo()
})
</script>

<template>
  <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">
    <div class="card w-full max-w-xl bg-base-100 shadow-xl">
      <div class="card-body">
        <h1 class="card-title text-2xl">Confirmar Convite</h1>

        <div v-if="loading" class="py-8 text-center">
          <span class="loading loading-spinner loading-md"></span>
        </div>

        <template v-else>
          <div v-if="error" class="alert alert-error">
            <span>{{ error }}</span>
          </div>
          <div v-if="success" class="alert alert-success">
            <span>{{ success }}</span>
          </div>

          <template v-if="info">
            <div class="bg-base-200 rounded-lg p-4 text-sm space-y-1">
              <p><strong>Convidado:</strong> {{ info.invited_email }}</p>
              <p><strong>Quem convidou:</strong> {{ info.owner_nome }} ({{ info.owner_email }})</p>
            </div>

            <div v-if="info.expired" class="alert alert-warning mt-4">
              <span>Este convite expirou. Solicite um novo convite.</span>
            </div>

            <form v-else class="space-y-4 mt-4" @submit.prevent="confirmar">
              <div v-if="!info.has_account" class="space-y-4">
                <p class="text-sm opacity-70">
                  Este e-mail ainda nao possui conta. Complete o cadastro para confirmar o convite.
                </p>
                <label class="form-control w-full">
                  <span class="label-text mb-1">Nome</span>
                  <input v-model="nome" class="input input-bordered w-full" required />
                </label>
                <label class="form-control w-full">
                  <span class="label-text mb-1">Senha</span>
                  <input v-model="password" type="password" class="input input-bordered w-full" required />
                </label>
                <label class="form-control w-full">
                  <span class="label-text mb-1">Confirmar senha</span>
                  <input v-model="confirmPassword" type="password" class="input input-bordered w-full" required />
                </label>
              </div>

              <div class="card-actions justify-end">
                <button type="submit" class="btn btn-primary" :disabled="confirming">
                  <span v-if="confirming" class="loading loading-spinner loading-sm"></span>
                  <span v-else>Confirmar Convite</span>
                </button>
                <button type="button" class="btn btn-ghost" @click="router.push('/login')">
                  Ir para Login
                </button>
              </div>
            </form>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>
