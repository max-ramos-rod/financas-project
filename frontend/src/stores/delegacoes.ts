import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '@/services/api'
import type { Delegacao, DelegacaoContextOption } from '@/types'

export const useDelegacoesStore = defineStore('delegacoes', () => {
  const convitesEnviados = ref<Delegacao[]>([])
  const convitesRecebidos = ref<Delegacao[]>([])
  const actAsOptions = ref<DelegacaoContextOption[]>([])
  const loading = ref(false)
  const error = ref('')

  const pendingInviteCount = computed(
    () => convitesRecebidos.value.filter((d) => d.status === 'pending').length,
  )

  async function fetchConvites(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const [sentRes, receivedRes] = await Promise.all([
        api.get('/delegacoes/sent'),
        api.get('/delegacoes/received'),
      ])
      convitesEnviados.value = (sentRes.data as { data: Delegacao[] }).data
      convitesRecebidos.value = (receivedRes.data as { data: Delegacao[] }).data
    } catch (err: any) {
      error.value = err?.response?.data?.detail || 'Falha ao carregar convites.'
    } finally {
      loading.value = false
    }
  }

  async function fetchActAsOptions(): Promise<void> {
    try {
      const res = await api.get('/delegacoes/act-as-options')
      actAsOptions.value = res.data
    } catch {
      actAsOptions.value = []
    }
  }

  async function fetchPendingInvites(): Promise<void> {
    try {
      const res = await api.get('/delegacoes/received')
      convitesRecebidos.value = (res.data as { data: Delegacao[] }).data
    } catch {
      // mantém valor atual em caso de falha
    }
  }

  function reset() {
    convitesEnviados.value = []
    convitesRecebidos.value = []
    actAsOptions.value = []
    error.value = ''
  }

  return {
    convitesEnviados,
    convitesRecebidos,
    actAsOptions,
    pendingInviteCount,
    loading,
    error,
    fetchConvites,
    fetchActAsOptions,
    fetchPendingInvites,
    reset,
  }
})
