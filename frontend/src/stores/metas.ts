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

  function reset() {
    metas.value = []
  }

  return { metas, loading, fetchMetas, reset }
})
