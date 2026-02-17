<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/services/api'
import type { Delegacao } from '@/types'

const loading = ref(false)
const error = ref('')
const success = ref('')
const convitesEnviados = ref<Delegacao[]>([])
const convitesRecebidos = ref<Delegacao[]>([])

const formatDate = (value?: string | null): string => {
  if (!value) return '-'
  return new Date(value).toLocaleDateString('pt-BR')
}

const carregarConvites = async () => {
  loading.value = true
  error.value = ''
  try {
    const [sentResponse, receivedResponse] = await Promise.all([
      api.get<Delegacao[]>('/delegacoes/sent'),
      api.get<Delegacao[]>('/delegacoes/received'),
    ])
    convitesEnviados.value = sentResponse.data
    convitesRecebidos.value = receivedResponse.data
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Falha ao carregar convites.'
  } finally {
    loading.value = false
  }
}

const aceitar = async (delegacaoId: number) => {
  error.value = ''
  success.value = ''
  try {
    await api.post(`/delegacoes/${delegacaoId}/accept`)
    success.value = 'Convite aceito com sucesso.'
    await carregarConvites()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Falha ao aceitar convite.'
  }
}

const revogar = async (delegacaoId: number) => {
  error.value = ''
  success.value = ''
  try {
    await api.post(`/delegacoes/${delegacaoId}/revoke`)
    success.value = 'Delegacao revogada com sucesso.'
    await carregarConvites()
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Falha ao revogar delegacao.'
  }
}

onMounted(() => {
  carregarConvites()
})
</script>

<template>
  <div class="min-h-screen bg-base-200 p-6">
    <div class="max-w-6xl mx-auto space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold">Convites e Delegacoes</h1>
        <button class="btn btn-outline btn-sm" :disabled="loading" @click="carregarConvites">
          Atualizar
        </button>
      </div>

      <div v-if="error" class="alert alert-error">
        <span>{{ error }}</span>
      </div>
      <div v-if="success" class="alert alert-success">
        <span>{{ success }}</span>
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <section class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title text-lg">Recebidos</h2>
            <p class="text-sm opacity-70">Convites enviados para o seu e-mail.</p>

            <div v-if="convitesRecebidos.length === 0" class="text-sm opacity-60 mt-4">
              Nenhum convite recebido.
            </div>

            <div v-else class="space-y-3 mt-2">
              <div
                v-for="item in convitesRecebidos"
                :key="item.id"
                class="border rounded-lg p-3 flex items-center justify-between gap-3"
              >
                <div>
                  <p class="font-medium">{{ item.owner?.nome || 'Usuario' }}</p>
                  <p class="text-xs opacity-70">{{ item.owner?.email }}</p>
                  <p class="text-xs mt-1">Criado em {{ formatDate(item.created_at) }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="badge badge-outline">{{ item.status }}</span>
                  <button
                    v-if="item.status === 'pending'"
                    class="btn btn-primary btn-sm"
                    @click="aceitar(item.id)"
                  >
                    Aceitar
                  </button>
                  <button
                    v-if="item.status !== 'revoked'"
                    class="btn btn-ghost btn-sm text-error"
                    @click="revogar(item.id)"
                  >
                    Revogar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section class="card bg-base-100 shadow">
          <div class="card-body">
            <h2 class="card-title text-lg">Enviados</h2>
            <p class="text-sm opacity-70">Convites que voce enviou para outros e-mails.</p>

            <div v-if="convitesEnviados.length === 0" class="text-sm opacity-60 mt-4">
              Nenhum convite enviado.
            </div>

            <div v-else class="space-y-3 mt-2">
              <div
                v-for="item in convitesEnviados"
                :key="item.id"
                class="border rounded-lg p-3 flex items-center justify-between gap-3"
              >
                <div>
                  <p class="font-medium">{{ item.invited_email }}</p>
                  <p class="text-xs opacity-70">Permissao: {{ item.can_write ? 'Leitura e escrita' : 'Somente leitura' }}</p>
                  <p class="text-xs mt-1">Criado em {{ formatDate(item.created_at) }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="badge badge-outline">{{ item.status }}</span>
                  <button
                    v-if="item.status !== 'revoked'"
                    class="btn btn-ghost btn-sm text-error"
                    @click="revogar(item.id)"
                  >
                    Revogar
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
