import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Transacao } from '@/types'

export const useTransacoesStore = defineStore('transacoes', () => {
  const transacoes = ref<Transacao[]>([])
  const loading = ref(false)

  let fetchPromise: Promise<void> | null = null

  async function fetchTransacoes(params: Record<string, unknown> = {}): Promise<void> {
    if (fetchPromise) return fetchPromise
    loading.value = true
    fetchPromise = api
      .get('/transacoes', { params })
      .then((res) => {
        transacoes.value = (res.data as { data: Transacao[] }).data
      })
      .finally(() => {
        loading.value = false
        fetchPromise = null
      })
    return fetchPromise
  }

  function reset() {
    transacoes.value = []
    fetchPromise = null
  }

  return { transacoes, loading, fetchTransacoes, reset }
})
