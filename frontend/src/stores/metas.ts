import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Meta } from '@/types'

export const useMetasStore = defineStore('metas', () => {
  const metas = ref<Meta[]>([])
  const loading = ref(false)

  let fetchPromise: Promise<void> | null = null

  async function fetchMetas(): Promise<void> {
    if (fetchPromise) return fetchPromise
    loading.value = true
    fetchPromise = api
      .get('/metas')
      .then((res) => {
        metas.value = (res.data as { data: Meta[] }).data
      })
      .finally(() => {
        loading.value = false
        fetchPromise = null
      })
    return fetchPromise
  }

  async function remover(id: number): Promise<void> {
    await api.delete(`/metas/${id}`)
    metas.value = metas.value.filter((m) => m.id !== id)
  }

  function reset() {
    metas.value = []
  }

  return { metas, loading, fetchMetas, remover, reset }
})
