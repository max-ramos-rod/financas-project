<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const route = useRoute()

const formatDateForInput = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const normalizeDateString = (value?: string | null): string | null => {
  if (!value) return null
  return value.slice(0, 10)
}

const parseInputDate = (value: string): Date => {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

// State
const loading = ref(false)
const editando = ref(false)
const metaId = ref<number | null>(null)

// Form data
const form = ref({
  nome: '',
  descricao: '',
  valor_alvo: null as number | null,
  valor_atual: 0,
  data_inicio: formatDateForInput(new Date()),
  data_fim: null as string | null,
  concluida: false,
  cor: '#10B981'
})

const showErrorModal = ref(false)
const errorMessages = ref<string[]>([])

function formatApiError(error: any): string[] {
  const detail = error?.response?.data?.detail
  if (!detail) return [error?.message || 'Erro desconhecido']
  if (Array.isArray(detail)) {
    return detail.map(d => {
      if (typeof d === 'string') return d
      if (d?.msg && d?.loc) return `${d.loc.join('.')} — ${d.msg}`
      return JSON.stringify(d)
    })
  }
  if (typeof detail === 'object') {
    if (detail.msg) return [detail.msg]
    return [JSON.stringify(detail)]
  }
  return [String(detail)]
}

// Cores pré-definidas
const coresPredefinidas = [
  '#10B981', // verde
  '#3B82F6', // azul
  '#F59E0B', // âmbar
  '#EF4444', // vermelho
  '#8B5CF6', // roxo
  '#EC4899', // rosa
  '#06B6D4', // cyan
]

// Computed - Validação
const formValido = computed(() => {
  return (
    form.value.nome &&
    form.value.valor_alvo &&
    form.value.valor_alvo > 0 &&
    form.value.data_inicio &&
    (!form.value.data_fim || form.value.data_fim >= form.value.data_inicio)
  )
})

// Carrega meta para edição
const carregarMeta = async (id: number) => {
  loading.value = true
  try {
    const res = await api.get(`/metas/${id}`)
    const m = res.data
    form.value = {
      nome: m.nome || '',
      descricao: m.descricao || '',
      valor_alvo: m.valor_alvo ?? null,
      valor_atual: m.valor_atual ?? 0,
      data_inicio: normalizeDateString(m.data_inicio) || formatDateForInput(new Date()),
      data_fim: normalizeDateString(m.data_fim),
      concluida: m.concluida ?? false,
      cor: m.cor || '#10B981'
    }
  } catch (error) {
    console.error('Erro ao carregar meta:', error)
    errorMessages.value = formatApiError(error)
    showErrorModal.value = true
  } finally {
    loading.value = false
  }
}

// Métodos
const salvar = async () => {
  if (!formValido.value) return

  loading.value = true

  try {
    // Envia datas como date (YYYY-MM-DD) para evitar drift de timezone.
    const dados = {
      nome: form.value.nome,
      descricao: form.value.descricao || undefined,
      valor_alvo: Number(form.value.valor_alvo),
      valor_atual: Number(form.value.valor_atual) || 0,
      data_inicio: form.value.data_inicio,
      data_fim: form.value.data_fim || undefined,
      concluida: form.value.concluida,
      cor: form.value.cor
    }

    if (editando.value && metaId.value) {
      await api.put(`/metas/${metaId.value}`, dados)
    } else {
      await api.post('/metas', dados)
    }

    router.push('/metas')
  } catch (error: any) {
    console.error('Erro ao salvar:', error)
    errorMessages.value = formatApiError(error)
    showErrorModal.value = true
  } finally {
    loading.value = false
  }
}

const cancelar = () => {
  router.back()
}

const calcularDiasRestantes = (): number | null => {
  if (!form.value.data_fim) return null
  const fim = parseInputDate(form.value.data_fim)
  const agora = new Date()
  agora.setHours(0, 0, 0, 0)
  const diferenca = fim.getTime() - agora.getTime()
  return Math.ceil(diferenca / (1000 * 60 * 60 * 24))
}

onMounted(() => {
  // Verifica se é edição via route.params.id
  if (route.params.id) {
    const id = parseInt(route.params.id as string)
    if (!Number.isNaN(id)) {
      editando.value = true
      metaId.value = id
      carregarMeta(id)
      return
    }
  }

  // Define data final padrão (daqui a 3 meses) — só se não estiver em edição
  const dataFim = new Date()
  dataFim.setMonth(dataFim.getMonth() + 3)
  form.value.data_fim = formatDateForInput(dataFim)
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
          <h1 class="text-2xl font-bold">{{ editando ? '✏️ Editar Meta' : '➕ Nova Meta' }}</h1>
        </div>
      </div>
    </div>

    <!-- Form -->
    <div class="container mx-auto px-4 py-8">
      <div class="max-w-2xl mx-auto">
        <form @submit.prevent="salvar" class="card bg-white shadow-lg">
          <div class="card-body space-y-6">
            <!-- Nome -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Nome da Meta *</span>
              </label>
              <input
                v-model="form.nome"
                type="text"
                placeholder="Ex: Viagem para Orlando, Carro novo, Férias..."
                class="input input-bordered w-full"
                required
              />
            </div>

            <!-- Descrição -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Descrição</span>
              </label>
              <textarea
                v-model="form.descricao"
                class="textarea textarea-bordered w-full"
                rows="2"
                placeholder="Detalhes sobre sua meta..."
              ></textarea>
            </div>

            <!-- Valores -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Valor Alvo -->
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Valor Alvo *</span>
                </label>
                <div class="relative">
                  <span class="absolute left-3 top-3 text-gray-500">R$</span>
                  <input
                    v-model.number="form.valor_alvo"
                    type="number"
                    step="0.01"
                    placeholder="0,00"
                    class="input input-bordered w-full pl-12"
                    required
                  />
                </div>
              </div>

              <!-- Valor Atual -->
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Valor Atual</span>
                </label>
                <div class="relative">
                  <span class="absolute left-3 top-3 text-gray-500">R$</span>
                  <input
                    v-model.number="form.valor_atual"
                    type="number"
                    step="0.01"
                    placeholder="0,00"
                    class="input input-bordered w-full pl-12"
                  />
                </div>
              </div>
            </div>

            <!-- Progresso Visual -->
            <div v-if="form.valor_alvo && form.valor_alvo > 0" class="alert">
              <div>
                <p class="mb-2">
                  <strong>Progresso:</strong>
                  {{ form.valor_atual && form.valor_alvo
                    ? `${((form.valor_atual / form.valor_alvo) * 100).toFixed(1)}%`
                    : '0%' }}
                </p>
                <progress
                  class="progress w-full h-2"
                  :value="form.valor_atual || 0"
                  :max="form.valor_alvo"
                ></progress>
              </div>
            </div>

            <!-- Datas -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Data Início -->
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Data Início *</span>
                </label>
                <input
                  v-model="form.data_inicio"
                  type="date"
                  class="input input-bordered w-full"
                  required
                />
              </div>

              <!-- Data Fim -->
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Data Fim</span>
                </label>
                <input
                  v-model="form.data_fim"
                  type="date"
                  class="input input-bordered w-full"
                />
              </div>
            </div>

            <!-- Dias Restantes -->
            <div v-if="form.data_fim && calcularDiasRestantes()" class="alert alert-info">
              <div>
                <p class="text-sm">
                  ⏰ <strong>{{ calcularDiasRestantes() }}</strong> dias restantes para completar esta meta
                </p>
              </div>
            </div>

            <!-- Cor -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Cor da Meta</span>
              </label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="cor in coresPredefinidas"
                  :key="cor"
                  type="button"
                  @click="form.cor = cor"
                  class="btn btn-sm btn-circle"
                  :style="{
                    backgroundColor: cor,
                    borderColor: form.cor === cor ? '#000' : 'transparent',
                    borderWidth: form.cor === cor ? '2px' : '1px'
                  }"
                  :title="cor"
                />
              </div>
              <p class="text-xs text-gray-500 mt-2">Cor selecionada: {{ form.cor }}</p>
            </div>

            <!-- Status -->
            <div>
              <label class="flex items-center gap-3 cursor-pointer">
                <input v-model="form.concluida" type="checkbox" class="checkbox" />
                <div>
                  <p class="font-medium">✅ Marcar como Concluída</p>
                  <p class="text-sm text-gray-500">Indique se esta meta já foi alcançada</p>
                </div>
              </label>
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
                {{ loading ? 'Salvando...' : (editando ? 'Atualizar Meta' : 'Criar Meta') }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal de Erro -->
    <div v-if="showErrorModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">❗ Erro ao salvar</h3>
        <div class="space-y-2 text-sm text-gray-700">
          <p v-for="(m, i) in errorMessages" :key="i">• {{ m }}</p>
        </div>
        <div class="modal-action mt-6">
          <button @click="showErrorModal = false" class="btn btn-ghost">Fechar</button>
        </div>
      </div>
      <form method="dialog" class="modal-backdrop">
        <button @click="showErrorModal = false">close</button>
      </form>
    </div>
  </div>
</template>
