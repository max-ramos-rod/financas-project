import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '@/services/api'
import type { Conta } from '@/types'

export const useContasStore = defineStore('contas', () => {
  const contas = ref<Conta[]>([])
  const loading = ref(false)

  const contasAtivas = computed(() => contas.value.filter((c) => c.ativa))
  const contasAtivas_semCartao = computed(() =>
    contas.value.filter((c) => c.ativa && c.tipo !== 'cartao_credito')
  )

  let fetchPromise: Promise<void> | null = null

  async function fetchContas(): Promise<void> {
    if (fetchPromise) return fetchPromise
    loading.value = true
    fetchPromise = api
      .get('/contas')
      .then((res) => {
        contas.value = (res.data as { data: Conta[] }).data
      })
      .finally(() => {
        loading.value = false
        fetchPromise = null
      })
    return fetchPromise
  }

  function reset() {
    contas.value = []
  }

  return {
    contas,
    loading,
    contasAtivas,
    contasAtivas_semCartao,
    fetchContas,
    reset,
  }
})
