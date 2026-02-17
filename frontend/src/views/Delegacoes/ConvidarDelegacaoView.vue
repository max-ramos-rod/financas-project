<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'
import type { DelegacaoInviteResponse } from '@/types'

const email = ref('')
const canWrite = ref(true)
const loading = ref(false)
const error = ref('')
const success = ref('')

const enviarConvite = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    const response = await api.post<DelegacaoInviteResponse>('/delegacoes/invite', {
      email: email.value,
      can_write: canWrite.value,
    })

    const { has_account, email_sent } = response.data
    success.value = has_account
      ? 'Convite criado. O e-mail de confirmacao foi processado para o usuario.'
      : 'Convite criado para novo e-mail. A pessoa podera confirmar e concluir cadastro pelo link.'

    if (!email_sent) {
      success.value += ' SMTP nao configurado no backend, entao o envio automatico nao ocorreu.'
    }

    email.value = ''
    canWrite.value = true
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Nao foi possivel enviar o convite.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-base-200 p-6">
    <div class="max-w-3xl mx-auto">
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h1 class="card-title text-2xl">Convidar Acesso</h1>
          <p class="text-sm opacity-70">
            Envie um convite para outro e-mail acessar seus dados financeiros com permissao controlada.
          </p>

          <div v-if="error" class="alert alert-error mt-4">
            <span>{{ error }}</span>
          </div>
          <div v-if="success" class="alert alert-success mt-4">
            <span>{{ success }}</span>
          </div>

          <form class="space-y-4 mt-4" @submit.prevent="enviarConvite">
            <label class="form-control w-full">
              <span class="label-text mb-1">E-mail convidado</span>
              <input
                v-model.trim="email"
                type="email"
                required
                placeholder="pessoa@exemplo.com"
                class="input input-bordered w-full"
              />
            </label>

            <label class="label cursor-pointer justify-start gap-3">
              <input v-model="canWrite" type="checkbox" class="checkbox checkbox-primary" />
              <span class="label-text">Permitir escrita (criar, editar e excluir dados)</span>
            </label>

            <div class="card-actions justify-end">
              <button type="submit" class="btn btn-primary" :disabled="loading">
                <span v-if="loading" class="loading loading-spinner loading-sm" />
                <span v-else>Enviar Convite</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
