import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Categoria } from '@/types'

export const useCategoriasStore = defineStore('categorias', () => {
  const categorias = ref<Categoria[]>([])
  const loading = ref(false)

  let fetchPromise: Promise<void> | null = null

  async function fetchCategorias(): Promise<void> {
    if (fetchPromise) return fetchPromise
    loading.value = true
    fetchPromise = api
      .get<Categoria[]>('/categorias')
      .then((res) => {
        categorias.value = res.data
      })
      .finally(() => {
        loading.value = false
        fetchPromise = null
      })
    return fetchPromise
  }

  function reset() {
    categorias.value = []
  }

  return {
    categorias,
    loading,
    fetchCategorias,
    reset,
  }
})
