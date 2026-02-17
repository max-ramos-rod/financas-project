<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import type { Categoria } from '@/types'

const router = useRouter()
const route = useRoute()

// State
const loading = ref(false)
const carregando = ref(true)
const categorias = ref<Categoria[]>([])
const editando = ref(false)
const orcamentoId = ref<number | null>(null)

// Form data
const form = ref({
  categoria_id: null as number | null,
  mes: new Date().getMonth() + 1,
  ano: new Date().getFullYear(),
  valor_planejado: null as number | null
})

// Computed - Validação
const formValido = computed(() => {
  return (
    form.value.categoria_id &&
    form.value.mes &&
    form.value.ano &&
    form.value.valor_planejado &&
    form.value.valor_planejado > 0
  )
})

// Computed - Categoria selecionada
const categoriaSelecionada = computed(() => {
  return categorias.value.find(c => c.id === form.value.categoria_id)
})

// Métodos
const fetchDados = async () => {
  carregando.value = true
  try {
    const categoriasRes = await api.get('/categorias')
    categorias.value = categoriasRes.data

    // Se for edição, carrega o orçamento
    if (editando.value && orcamentoId.value) {
      await carregarOrcamento()
    }
  } catch (error) {
    console.error('Erro ao carregar dados:', error)
  } finally {
    carregando.value = false
  }
}

const carregarOrcamento = async () => {
  if (!orcamentoId.value) return
  
  try {
    const res = await api.get(`/orcamentos/${orcamentoId.value}`)
    const o = res.data
    form.value = {
      categoria_id: o.categoria_id,
      mes: o.mes,
      ano: o.ano,
      valor_planejado: o.valor_planejado
    }
  } catch (error) {
    console.error('Erro ao carregar orçamento:', error)
    alert('Erro ao carregar orçamento')
    router.back()
  }
}

const salvar = async () => {
  if (!formValido.value) return
  
  loading.value = true
  
  try {
    const dados = {
      categoria_id: form.value.categoria_id,
      mes: form.value.mes,
      ano: form.value.ano,
      valor_planejado: Number(form.value.valor_planejado)
    }
    
    if (editando.value && orcamentoId.value) {
      await api.put(`/orcamentos/${orcamentoId.value}`, dados)
    } else {
      await api.post('/orcamentos', dados)
    }
    
    router.push('/orcamentos')
  } catch (error: any) {
    console.error('Erro ao salvar:', error)
    alert(error.response?.data?.detail || 'Erro ao salvar orçamento')
  } finally {
    loading.value = false
  }
}

const cancelar = () => {
  router.back()
}

const formatarMoeda = (valor: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(valor)
}

const getMeses = () => [
  { valor: 1, label: 'Janeiro' },
  { valor: 2, label: 'Fevereiro' },
  { valor: 3, label: 'Março' },
  { valor: 4, label: 'Abril' },
  { valor: 5, label: 'Maio' },
  { valor: 6, label: 'Junho' },
  { valor: 7, label: 'Julho' },
  { valor: 8, label: 'Agosto' },
  { valor: 9, label: 'Setembro' },
  { valor: 10, label: 'Outubro' },
  { valor: 11, label: 'Novembro' },
  { valor: 12, label: 'Dezembro' }
]

onMounted(() => {
  // Verifica se é edição
  if (route.params.id) {
    editando.value = true
    orcamentoId.value = parseInt(route.params.id as string)
  }
  
  fetchDados()
})
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <!-- Header -->
    <div class="bg-white shadow">
      <div class="container mx-auto px-4 py-4">
        <div class="flex items-center gap-4">
          <button @click="cancelar" class="btn btn-ghost btn-sm">
            ← Voltar
          </button>
          <h1 class="text-2xl font-bold">
            {{ editando ? '✏️ Editar Orçamento' : '➕ Novo Orçamento' }}
          </h1>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="carregando" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
      <p class="mt-4">Carregando...</p>
    </div>

    <!-- Form -->
    <div v-else class="container mx-auto px-4 py-8">
      <div class="max-w-2xl mx-auto">
        <form @submit.prevent="salvar" class="card bg-white shadow-lg">
          <div class="card-body space-y-6">
            
            <!-- Categoria -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Categoria *</span>
              </label>
              <select v-model.number="form.categoria_id" class="select select-bordered w-full" required>
                <option :value="null">Selecione uma categoria...</option>
                <option v-for="cat in categorias" :key="cat.id" :value="cat.id">
                  {{ cat.icone }} {{ cat.nome }}
                </option>
              </select>
            </div>

            <!-- Período -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Mês -->
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Mês *</span>
                </label>
                <select v-model.number="form.mes" class="select select-bordered w-full" required>
                  <option v-for="mes in getMeses()" :key="mes.valor" :value="mes.valor">
                    {{ mes.label }}
                  </option>
                </select>
              </div>

              <!-- Ano -->
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Ano *</span>
                </label>
                <input
                  v-model.number="form.ano"
                  type="number"
                  min="2000"
                  max="2100"
                  class="input input-bordered w-full"
                  required
                />
              </div>
            </div>

            <!-- Valor Planejado -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Valor Planejado *</span>
              </label>
              <div class="relative">
                <span class="absolute left-3 top-3 text-gray-500">R$</span>
                <input
                  v-model.number="form.valor_planejado"
                  type="number"
                  step="0.01"
                  placeholder="0,00"
                  class="input input-bordered w-full pl-12"
                  required
                />
              </div>
              <p v-if="form.valor_planejado" class="text-sm text-gray-500 mt-2">
                Valor: <strong>{{ formatarMoeda(form.valor_planejado) }}</strong>
              </p>
            </div>

            <!-- Preview -->
            <div class="divider">Preview</div>

            <div class="card bg-base-300">
              <div class="card-body">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <span class="text-3xl">{{ categoriaSelecionada?.icone || '📌' }}</span>
                    <div>
                      <p class="font-semibold">{{ categoriaSelecionada?.nome || 'Selecione uma categoria' }}</p>
                      <p class="text-sm text-gray-600">
                        {{ getMeses().find(m => m.valor === form.mes)?.label || 'Mês' }} de {{ form.ano }}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="mt-4 p-3 rounded-lg bg-base-100">
                  <p class="text-sm text-gray-600 mb-1">Valor Planejado</p>
                  <p class="text-2xl font-bold text-info">
                    {{ form.valor_planejado ? formatarMoeda(form.valor_planejado) : 'R$ 0,00' }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Botões -->
            <div class="card-actions justify-end pt-4 border-t">
              <button
                type="button"
                @click="cancelar"
                class="btn btn-ghost"
                :disabled="loading"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="!formValido || loading"
              >
                <span v-if="loading" class="loading loading-spinner"></span>
                {{ loading ? 'Salvando...' : (editando ? 'Atualizar Orçamento' : 'Criar Orçamento') }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>