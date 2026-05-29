import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Orcamento } from '@/types'

export const useOrcamentosStore = defineStore('orcamentos', () => {
  const orcamentos = ref<Orcamento[]>([])
  const loading = ref(false)

  async function fetchOrcamentos(params?: { mes?: number; ano?: number }): Promise<void> {
    loading.value = true
    try {
      const res = await api.get('/orcamentos', { params })
      orcamentos.value = (res.data as { data: Orcamento[] }).data
    } finally {
      loading.value = false
    }
  }

  function reset() {
    orcamentos.value = []
  }

  return { orcamentos, loading, fetchOrcamentos, reset }
})
