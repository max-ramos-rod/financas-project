<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'

const router = useRouter()
const route = useRoute()

// State
const loading = ref(false)
const editando = ref(false)
const contaId = ref<number | null>(null)

// Form data
const form = ref({
  nome: '',
  tipo: 'conta_corrente' as 'carteira' | 'conta_corrente' | 'poupanca' | 'cartao_credito' | 'investimento' | 'outro',
  saldo: 0,
  dia_fechamento: null as number | null,
  dia_vencimento: null as number | null,
  limite_credito: null as number | null,
  cor: '#3B82F6',
  ativa: true
})

// Cores pre-definidas
const coresPredefinidas = [
  '#3B82F6', // azul
  '#10B981', // verde
  '#F59E0B', // ambar
  '#EF4444', // vermelho
  '#8B5CF6', // roxo
  '#EC4899', // rosa
  '#06B6D4', // cyan
  '#6B7280', // cinza
]

// Tipos de conta
const tiposConta = [
  { valor: 'carteira', label: 'Carteira', descricao: 'Dinheiro em mao' },
  { valor: 'conta_corrente', label: 'Conta Corrente', descricao: 'Conta bancaria' },
  { valor: 'poupanca', label: 'Poupanca', descricao: 'Conta de poupanca' },
  { valor: 'cartao_credito', label: 'Cartao de Credito', descricao: 'Compras para fatura' },
  { valor: 'investimento', label: 'Investimento', descricao: 'Aplicacoes financeiras' },
  { valor: 'outro', label: 'Outro', descricao: 'Outra conta' },
]

// Computed - Validacao
const formValido = computed(() => {
  const base = (
    form.value.nome &&
    form.value.tipo &&
    form.value.saldo !== null
  )
  if (!base) return false
  if (form.value.tipo === 'cartao_credito') {
    return !!form.value.dia_fechamento && !!form.value.dia_vencimento
  }
  return true
})

const isCartaoCredito = computed(() => form.value.tipo === 'cartao_credito')

watch(
  () => form.value.tipo,
  (tipo) => {
    if (tipo === 'cartao_credito') {
      form.value.saldo = 0
    }
  }
)

// Metodos
const carregarConta = async () => {
  if (!contaId.value) return
  
  try {
    const res = await api.get(`/contas/${contaId.value}`)
    const conta = res.data
    form.value = {
      nome: conta.nome,
      tipo: conta.tipo,
      saldo: conta.saldo,
      dia_fechamento: conta.dia_fechamento ?? null,
      dia_vencimento: conta.dia_vencimento ?? null,
      limite_credito: conta.limite_credito ?? null,
      cor: conta.cor,
      ativa: conta.ativa
    }
  } catch (error) {
    console.error('Erro ao carregar conta:', error)
    alert('Erro ao carregar conta')
    router.back()
  }
}

const salvar = async () => {
  if (!formValido.value) return
  
  loading.value = true
  
  try {
    const dados = {
      nome: form.value.nome,
      tipo: form.value.tipo,
      saldo: form.value.tipo === 'cartao_credito' ? 0 : Number(form.value.saldo),
      dia_fechamento: form.value.tipo === 'cartao_credito' ? form.value.dia_fechamento : null,
      dia_vencimento: form.value.tipo === 'cartao_credito' ? form.value.dia_vencimento : null,
      limite_credito: form.value.tipo === 'cartao_credito' ? form.value.limite_credito : null,
      cor: form.value.cor,
      ativa: form.value.ativa
    }
    
    if (editando.value && contaId.value) {
      await api.put(`/contas/${contaId.value}`, dados)
    } else {
      await api.post('/contas', dados)
    }
    
    router.push('/contas')
  } catch (error: any) {
    console.error('Erro ao salvar:', error)
    alert(error.response?.data?.detail || 'Erro ao salvar conta')
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

onMounted(() => {
  // Verifica se e edicao
  if (route.params.id) {
    editando.value = true
    contaId.value = parseInt(route.params.id as string)
    carregarConta()
  }
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
            {{ editando ? '✏️ Editar Conta' : '➕ Nova Conta' }}
          </h1>
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
                <span class="label-text font-semibold">Nome da Conta *</span>
              </label>
              <input
                v-model="form.nome"
                type="text"
                placeholder="Ex: Meu Banco, Carteira, Poupanca..."
                class="input input-bordered w-full"
                required
              />
            </div>

            <!-- Tipo de Conta -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Tipo de Conta *</span>
              </label>
              <div class="space-y-2">
                <div v-for="tipo in tiposConta" :key="tipo.valor" class="form-control">
                  <label class="label cursor-pointer">
                    <span class="label-text">
                      <span class="font-medium">{{ tipo.label }}</span>
                      <span class="text-xs text-gray-500 block">{{ tipo.descricao }}</span>
                    </span>
                    <input
                      v-model="form.tipo"
                      type="radio"
                      :value="tipo.valor"
                      class="radio radio-primary"
                    />
                  </label>
                </div>
              </div>
            </div>

            <!-- Saldo Inicial -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Saldo *</span>
              </label>
              <div class="relative">
                <span class="absolute left-3 top-3 text-gray-500">R$</span>
                <input
                  v-model.number="form.saldo"
                  type="number"
                  step="0.01"
                  placeholder="0,00"
                  class="input input-bordered w-full pl-12"
                  :disabled="isCartaoCredito"
                  required
                />
              </div>
              <p v-if="isCartaoCredito" class="text-sm text-gray-500 mt-2">
                Em cartao de credito o saldo inicial e fixo em <strong>R$ 0,00</strong>.
              </p>
              <p v-if="form.saldo !== null" class="text-sm text-gray-500 mt-2">
                Saldo atual: <strong>{{ formatarMoeda(form.saldo) }}</strong>
              </p>
            </div>

            <div v-if="form.tipo === 'cartao_credito'" class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Dia Fechamento *</span>
                </label>
                <input v-model.number="form.dia_fechamento" type="number" min="1" max="31" class="input input-bordered w-full" />
              </div>
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Dia Vencimento *</span>
                </label>
                <input v-model.number="form.dia_vencimento" type="number" min="1" max="31" class="input input-bordered w-full" />
              </div>
              <div>
                <label class="label">
                  <span class="label-text font-semibold">Limite Credito</span>
                </label>
                <input v-model.number="form.limite_credito" type="number" min="0" step="0.01" class="input input-bordered w-full" />
              </div>
            </div>

            <!-- Cor -->
            <div>
              <label class="label">
                <span class="label-text font-semibold">Cor da Conta</span>
              </label>
              <div class="flex flex-wrap gap-3 mb-4">
                <button
                  v-for="cor in coresPredefinidas"
                  :key="cor"
                  type="button"
                  @click="form.cor = cor"
                  class="btn btn-sm btn-circle"
                  :style="{ 
                    backgroundColor: cor,
                    borderColor: form.cor === cor ? '#000' : 'transparent',
                    borderWidth: form.cor === cor ? '3px' : '1px'
                  }"
                  :title="cor"
                />
              </div>
              <p class="text-xs text-gray-500">Cor selecionada: {{ form.cor }}</p>
            </div>

            <!-- Status -->
            <div>
              <label class="flex items-center gap-3 cursor-pointer">
                <input v-model="form.ativa" type="checkbox" class="checkbox" />
                <div>
                  <p class="font-medium">✅ Conta Ativa</p>
                  <p class="text-sm text-gray-500">Marque para usar esta conta</p>
                </div>
              </label>
            </div>

            <!-- Preview -->
            <div class="divider">Preview</div>

            <div
              class="card shadow-md"
              :style="{ borderLeft: `5px solid ${form.cor}` }"
            >
              <div class="card-body">
                <div class="flex justify-between items-start">
                  <div>
                    <h3 class="card-title text-lg">{{ form.nome || 'Nome da Conta' }}</h3>
                    <p class="text-sm text-gray-500 mt-1">
                      {{ tiposConta.find(t => t.valor === form.tipo)?.label || 'Tipo' }}
                    </p>
                  </div>
                  <div v-if="form.ativa" class="badge badge-success">✅ Ativa</div>
                  <div v-else class="badge badge-ghost">❌ Inativa</div>
                </div>
                <div class="mt-4 p-3 rounded-lg bg-gray-50">
                  <p class="text-sm text-gray-500 mb-1">Saldo</p>
                  <p class="text-3xl font-bold text-success">
                    {{ formatarMoeda(form.saldo) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Botoes -->
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
                {{ loading ? 'Salvando...' : (editando ? 'Atualizar Conta' : 'Criar Conta') }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

