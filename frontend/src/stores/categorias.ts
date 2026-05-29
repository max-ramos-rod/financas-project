import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import type { Categoria } from '@/types'

type CategoriaPayload = { nome: string; icone?: string; cor?: string; tipo: string }

export const useCategoriasStore = defineStore('categorias', () => {
  const categorias = ref<Categoria[]>([])
  const loading = ref(false)

  let fetchPromise: Promise<void> | null = null

  async function fetchCategorias(): Promise<void> {
    if (fetchPromise) return fetchPromise
    loading.value = true
    fetchPromise = api
      .get('/categorias')
      .then((res) => {
        categorias.value = (res.data as { data: Categoria[] }).data
      })
      .finally(() => {
        loading.value = false
        fetchPromise = null
      })
    return fetchPromise
  }

  async function criar(data: CategoriaPayload): Promise<Categoria> {
    const res = await api.post<Categoria>('/categorias', data)
    await fetchCategorias()
    return res.data
  }

  async function atualizar(id: number, data: Partial<CategoriaPayload>): Promise<Categoria> {
    const res = await api.put<Categoria>(`/categorias/${id}`, data)
    await fetchCategorias()
    return res.data
  }

  async function remover(id: number): Promise<void> {
    await api.delete(`/categorias/${id}`)
    categorias.value = categorias.value.filter((c) => c.id !== id)
  }

  function reset() {
    categorias.value = []
  }

  return {
    categorias,
    loading,
    fetchCategorias,
    criar,
    atualizar,
    remover,
    reset,
  }
})
