<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import type { Categoria } from '@/types'
import { extractApiError } from '@/services/apiError'
import ConfirmModal from '@/components/ui/ConfirmModal.vue'
import { useCategoriasStore } from '@/stores/categorias'

const categoriasStore = useCategoriasStore()
const { categorias, loading } = storeToRefs(categoriasStore)
const salvando = ref(false)
const erro = ref('')

const filtros = ref({
  busca: '',
  tipo: 'todas' as 'todas' | 'entrada' | 'saida' | 'transferencia',
})

const showModal = ref(false)
const editandoId = ref<number | null>(null)
const form = ref({
  nome: '',
  icone: 'tag',
  cor: '#6B7280',
  tipo: 'saida' as 'entrada' | 'saida' | 'transferencia',
})

const categoriasFiltradas = computed(() => {
  let items = [...categorias.value]
  if (filtros.value.tipo !== 'todas') {
    items = items.filter((c) => c.tipo === filtros.value.tipo)
  }
  if (filtros.value.busca.trim()) {
    const q = filtros.value.busca.trim().toLowerCase()
    items = items.filter((c) => c.nome.toLowerCase().includes(q))
  }
  return items.sort((a, b) => a.nome.localeCompare(b.nome))
})

const minhasCategorias = computed(() => categoriasFiltradas.value.filter((c) => !c.padrao))
const categoriasPadrao = computed(() => categoriasFiltradas.value.filter((c) => c.padrao))

const fetchCategorias = () => categoriasStore.fetchCategorias()

const abrirNovaCategoria = () => {
  editandoId.value = null
  form.value = {
    nome: '',
    icone: 'tag',
    cor: '#6B7280',
    tipo: 'saida',
  }
  erro.value = ''
  showModal.value = true
}

const abrirEditarCategoria = (categoria: Categoria) => {
  editandoId.value = categoria.id
  form.value = {
    nome: categoria.nome,
    icone: categoria.icone || 'tag',
    cor: categoria.cor || '#6B7280',
    tipo: (categoria.tipo as 'entrada' | 'saida' | 'transferencia') || 'saida',
  }
  erro.value = ''
  showModal.value = true
}

const fecharModal = () => {
  showModal.value = false
}

const salvarCategoria = async () => {
  if (!form.value.nome.trim()) return
  salvando.value = true
  erro.value = ''
  try {
    const payload = {
      nome: form.value.nome.trim(),
      icone: form.value.icone.trim() || 'tag',
      cor: form.value.cor,
      tipo: form.value.tipo,
    }
    if (editandoId.value) {
      await categoriasStore.atualizar(editandoId.value, payload)
    } else {
      await categoriasStore.criar(payload)
    }
    showModal.value = false
  } catch (error) {
    erro.value = extractApiError(error, 'Erro ao salvar categoria')
  } finally {
    salvando.value = false
  }
}

const categoriaAExcluir = ref<Categoria | null>(null)
const showExcluirModal = ref(false)

const iniciarExclusao = (categoria: Categoria) => {
  if (categoria.padrao) return
  categoriaAExcluir.value = categoria
  showExcluirModal.value = true
}

const confirmarExcluir = async () => {
  if (!categoriaAExcluir.value) return
  try {
    await categoriasStore.remover(categoriaAExcluir.value.id)
  } catch (error) {
    erro.value = extractApiError(error, 'Erro ao excluir categoria')
  }
}

onMounted(fetchCategorias)
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <div v-if="loading" class="container mx-auto px-4 py-12 text-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else class="container mx-auto px-4 py-6 space-y-6">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-semibold">Categorias</h1>
        <button class="btn btn-primary btn-sm" @click="abrirNovaCategoria">Nova categoria</button>
      </div>

      <div v-if="erro" class="alert alert-error">
        <span>{{ erro }}</span>
      </div>

      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input v-model="filtros.busca" class="input input-bordered md:col-span-2" placeholder="Buscar categoria" />
            <select v-model="filtros.tipo" class="select select-bordered">
              <option value="todas">Todos os tipos</option>
              <option value="entrada">Entrada</option>
              <option value="saida">Saída</option>
              <option value="transferencia">Transferência</option>
            </select>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title">Minhas categorias</h2>
            <div v-if="minhasCategorias.length === 0" class="text-sm text-base-content/50">Nenhuma categoria criada.</div>
            <div v-else class="space-y-2">
              <div v-for="c in minhasCategorias" :key="c.id" class="border rounded p-3 flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <span class="badge badge-outline">{{ c.tipo }}</span>
                  <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: c.cor }"></span>
                  <span>{{ c.icone }} {{ c.nome }}</span>
                </div>
                <div class="flex gap-2">
                  <button class="btn btn-xs" @click="abrirEditarCategoria(c)">Editar</button>
                  <button class="btn btn-xs btn-error" @click="iniciarExclusao(c)">Excluir</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title">Categorias padrão</h2>
            <div v-if="categoriasPadrao.length === 0" class="text-sm text-base-content/50">Nenhuma categoria padrão encontrada.</div>
            <div v-else class="space-y-2">
              <div v-for="c in categoriasPadrao" :key="c.id" class="border rounded p-3 flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <span class="badge badge-ghost">{{ c.tipo }}</span>
                  <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: c.cor }"></span>
                  <span>{{ c.icone }} {{ c.nome }}</span>
                </div>
                <span class="text-xs opacity-70">Somente leitura</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">{{ editandoId ? 'Editar categoria' : 'Nova categoria' }}</h3>
        <div class="space-y-3">
          <div>
            <label class="label"><span class="label-text">Nome</span></label>
            <input v-model="form.nome" class="input input-bordered w-full" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label"><span class="label-text">Ícone</span></label>
              <input v-model="form.icone" class="input input-bordered w-full" />
            </div>
            <div>
              <label class="label"><span class="label-text">Cor</span></label>
              <input v-model="form.cor" type="color" class="input input-bordered w-full p-1 h-11" />
            </div>
          </div>
          <div>
            <label class="label"><span class="label-text">Tipo</span></label>
            <select v-model="form.tipo" class="select select-bordered w-full">
              <option value="entrada">Entrada</option>
              <option value="saida">Saída</option>
              <option value="transferencia">Transferência</option>
            </select>
          </div>
        </div>
        <div class="modal-action">
          <button class="btn btn-ghost" @click="fecharModal" :disabled="salvando">Cancelar</button>
          <button class="btn btn-primary" @click="salvarCategoria" :disabled="salvando || !form.nome.trim()">
            {{ salvando ? 'Salvando...' : 'Salvar' }}
          </button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="fecharModal">close</button>
      </form>
    </div>

    <ConfirmModal
      v-model:open="showExcluirModal"
      severity="simple"
      :title="`Excluir '${categoriaAExcluir?.nome ?? ''}'?`"
      description="Esta ação não pode ser desfeita."
      confirm-label="Excluir"
      cancel-label="Cancelar"
      @confirm="confirmarExcluir"
    />
  </div>
</template>
