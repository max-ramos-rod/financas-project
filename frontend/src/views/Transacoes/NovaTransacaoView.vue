<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import type { Conta, Categoria, Meta } from '@/types'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const carregando = ref(true)
const contas = ref<Conta[]>([])
const categorias = ref<Categoria[]>([])
const metas = ref<Meta[]>([])
const modoCristao = ref(import.meta.env.VITE_MODO_CRISTAO === 'true')
const editando = ref(false)
const transacaoId = ref<number | null>(null)
const showCategoriaModal = ref(false)
const criandoCategoria = ref(false)
const erroCategoria = ref('')

const formatDateForInput = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const form = ref({
  conta_id: null as number | null,
  categoria_id: null as number | null,
  descricao: '',
  valor: null as number | null,
  tipo: 'saida' as 'entrada' | 'saida',
  data: formatDateForInput(new Date()),
  data_vencimento: formatDateForInput(new Date()),
  data_liquidacao: null as string | null,
  status_liquidacao: 'previsto' as 'previsto' | 'liquidado' | 'atrasado' | 'cancelado',
  fixa: false,
  recorrente: false,
  confirmada: true,
  tem_dizimo: false,
  percentual_dizimo: 10.0,
  parcelado: false,
  total_parcelas: null as number | null,
  e_emprestimo: false,
  pessoa_emprestimo: '',
  observacoes: '',
  tags: '',
  valor_multa: 0,
  valor_juros: 0,
  valor_desconto: 0,
  meta_id: null as number | null,
})

const formCategoria = ref({
  nome: '',
  icone: '📌',
  cor: '#6B7280',
})

const categoriasFiltradas = computed(() => categorias.value.filter((c) => c.tipo === form.value.tipo || c.tipo === null))

const formValido = computed(() => {
  const base = form.value.conta_id && form.value.descricao && form.value.valor && form.value.valor > 0 && form.value.data
  if (!base) return false
  if (form.value.parcelado) {
    return !!form.value.total_parcelas && form.value.total_parcelas >= 2
  }
  return true
})

const valorDizimo = computed(() => {
  if (!form.value.tem_dizimo || !form.value.valor) return 0
  return (form.value.valor * form.value.percentual_dizimo) / 100
})

const valorParcela = computed(() => {
  if (!form.value.parcelado || !form.value.valor) return 0
  return Number(form.value.valor)
})

const valorEfetivo = computed(() => {
  if (!form.value.valor) return 0
  return Math.max(0, Number(form.value.valor) + Number(form.value.valor_multa || 0) + Number(form.value.valor_juros || 0) - Number(form.value.valor_desconto || 0))
})

const valorTotalParcelado = computed(() => {
  if (!form.value.parcelado || !form.value.total_parcelas || !form.value.valor) return 0
  return Number(form.value.valor) * Number(form.value.total_parcelas)
})

const contaSelecionada = computed(() => contas.value.find((c) => c.id === form.value.conta_id) || null)
const isCartaoCredito = computed(() => contaSelecionada.value?.tipo === 'cartao_credito')
const statusBloqueado = computed(() => isCartaoCredito.value && form.value.tipo === 'saida')

watch(
  () => [form.value.conta_id, form.value.tipo],
  () => {
    if (isCartaoCredito.value && form.value.tipo === 'saida') {
      form.value.status_liquidacao = 'previsto'
      form.value.data_liquidacao = null
    }
  }
)

const fetchDados = async () => {
  carregando.value = true
  try {
    const [contasRes, categoriasRes, metasRes] = await Promise.all([
      api.get('/contas'),
      api.get('/categorias'),
      api.get('/metas'),
    ])

    contas.value = contasRes.data
    categorias.value = categoriasRes.data
    metas.value = metasRes.data

    const primeiraAtiva = contas.value.find((c) => c.ativa)
    if (primeiraAtiva && !editando.value) {
      form.value.conta_id = primeiraAtiva.id
    }

    if (editando.value && transacaoId.value) {
      await carregarTransacao()
    }
  } finally {
    carregando.value = false
  }
}

const carregarTransacao = async () => {
  if (!transacaoId.value) return
  const res = await api.get(`/transacoes/${transacaoId.value}`)
  const t = res.data

  form.value = {
    conta_id: t.conta_id,
    categoria_id: t.categoria_id,
    descricao: t.descricao,
    valor: t.valor,
    tipo: t.tipo,
    data: t.data,
    data_vencimento: t.data_vencimento || t.data,
    data_liquidacao: t.data_liquidacao || null,
    status_liquidacao: t.status_liquidacao || 'previsto',
    fixa: t.fixa,
    recorrente: t.recorrente,
    confirmada: t.confirmada,
    tem_dizimo: t.tem_dizimo || false,
    percentual_dizimo: t.percentual_dizimo || 10,
    parcelado: t.parcelado || false,
    total_parcelas: t.total_parcelas || null,
    e_emprestimo: t.e_emprestimo || false,
    pessoa_emprestimo: t.pessoa_emprestimo || '',
    observacoes: t.observacoes || '',
    tags: t.tags || '',
    valor_multa: t.valor_multa || 0,
    valor_juros: t.valor_juros || 0,
    valor_desconto: t.valor_desconto || 0,
    meta_id: t.meta_id || null,
  }
}

const abrirModalCategoria = () => {
  erroCategoria.value = ''
  formCategoria.value = {
    nome: '',
    icone: '📌',
    cor: '#6B7280',
  }
  showCategoriaModal.value = true
}

const fecharModalCategoria = () => {
  showCategoriaModal.value = false
}

const salvarCategoria = async () => {
  if (!formCategoria.value.nome.trim()) return
  criandoCategoria.value = true
  erroCategoria.value = ''
  try {
    const payload = {
      nome: formCategoria.value.nome.trim(),
      icone: formCategoria.value.icone.trim() || '📌',
      cor: formCategoria.value.cor,
      tipo: form.value.tipo,
    }
    const res = await api.post('/categorias', payload)
    categorias.value.push(res.data)
    form.value.categoria_id = res.data.id
    showCategoriaModal.value = false
  } catch (error: any) {
    erroCategoria.value = error?.response?.data?.detail || 'Erro ao criar categoria'
  } finally {
    criandoCategoria.value = false
  }
}

const salvar = async () => {
  if (!formValido.value) return
  loading.value = true

  try {
    const dados = {
      conta_id: form.value.conta_id,
      categoria_id: form.value.categoria_id,
      descricao: form.value.descricao,
      valor: Number(form.value.valor),
      tipo: form.value.tipo,
      data: form.value.data,
      data_vencimento: form.value.data_vencimento || undefined,
      data_liquidacao: form.value.status_liquidacao === 'liquidado' ? (form.value.data_liquidacao || form.value.data) : undefined,
      status_liquidacao: form.value.status_liquidacao,
      fixa: form.value.fixa,
      recorrente: form.value.recorrente,
      confirmada: form.value.confirmada,
      tem_dizimo: form.value.tipo === 'entrada' ? form.value.tem_dizimo : false,
      percentual_dizimo: form.value.tem_dizimo ? form.value.percentual_dizimo : undefined,
      parcelado: form.value.parcelado,
      total_parcelas: form.value.parcelado ? form.value.total_parcelas : undefined,
      e_emprestimo: form.value.e_emprestimo,
      pessoa_emprestimo: form.value.e_emprestimo ? form.value.pessoa_emprestimo : undefined,
      observacoes: form.value.observacoes.trim() || undefined,
      tags: form.value.tags.trim() || undefined,
      valor_multa: form.value.valor_multa || 0,
      valor_juros: form.value.valor_juros || 0,
      valor_desconto: form.value.valor_desconto || 0,
      meta_id: form.value.meta_id,
    }

    if (editando.value && transacaoId.value) {
      await api.put(`/transacoes/${transacaoId.value}`, dados)
    } else {
      await api.post('/transacoes', dados)
    }

    router.push('/transacoes')
  } catch (error: any) {
    alert(error?.response?.data?.detail || 'Erro ao salvar transacao')
  } finally {
    loading.value = false
  }
}

const cancelar = () => router.back()

const formatarMoeda = (valor: number): string => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)
}

onMounted(() => {
  if (route.params.id) {
    editando.value = true
    transacaoId.value = parseInt(route.params.id as string, 10)
  }
  fetchDados()
})
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <div class="bg-white shadow">
      <div class="container mx-auto px-4 py-4 flex items-center gap-4">
        <button @click="cancelar" class="btn btn-ghost btn-sm">Voltar</button>
        <h1 class="text-2xl font-bold">{{ editando ? 'Editar Transacao' : 'Nova Transacao' }}</h1>
      </div>
    </div>

    <div v-if="carregando" class="container mx-auto px-4 py-16 text-center">
      <span class="loading loading-spinner loading-lg"></span>
    </div>

    <div v-else class="container mx-auto px-4 py-8">
      <form @submit.prevent="salvar" class="card bg-white shadow-lg max-w-3xl mx-auto">
        <div class="card-body space-y-5">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="md:col-span-2">
              <label class="label"><span class="label-text font-semibold">Descricao *</span></label>
              <input v-model="form.descricao" class="input input-bordered w-full" required />
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">{{ form.parcelado ? 'Valor da parcela *' : 'Valor *' }}</span></label>
              <input v-model.number="form.valor" type="number" step="0.01" class="input input-bordered w-full" required />
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">Tipo *</span></label>
              <select v-model="form.tipo" class="select select-bordered w-full">
                <option value="entrada">Entrada</option>
                <option value="saida">Saida</option>
              </select>
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">Data *</span></label>
              <input v-model="form.data" type="date" class="input input-bordered w-full" required />
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">Vencimento</span></label>
              <input v-model="form.data_vencimento" type="date" class="input input-bordered w-full" />
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">Conta *</span></label>
              <select v-model="form.conta_id" class="select select-bordered w-full" required>
                <option :value="null">Selecione...</option>
                <option v-for="conta in contas.filter((c) => c.ativa)" :key="conta.id" :value="conta.id">{{ conta.nome }}</option>
              </select>
              <p v-if="isCartaoCredito && form.tipo === 'saida'" class="text-xs text-gray-500 mt-1">
                Conta cartao: compra registrada para pagamento da fatura.
              </p>
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">Status</span></label>
              <select v-model="form.status_liquidacao" class="select select-bordered w-full" :disabled="statusBloqueado">
                <option value="previsto">{{ form.tipo === 'entrada' ? 'Previsto' : 'A pagar' }}</option>
                <option value="liquidado">{{ form.tipo === 'entrada' ? 'Recebido' : 'Pago' }}</option>
                <option value="atrasado">Atrasado</option>
                <option value="cancelado">Cancelado</option>
              </select>
              <p v-if="statusBloqueado" class="text-xs text-gray-500 mt-1">
                Para cartao de credito, o status inicial e sempre A pagar.
              </p>
            </div>
            <div v-if="form.status_liquidacao === 'liquidado'">
              <label class="label"><span class="label-text font-semibold">Data liquidacao</span></label>
              <input v-model="form.data_liquidacao" type="date" class="input input-bordered w-full" />
            </div>
            <div>
              <label class="label"><span class="label-text font-semibold">Categoria</span></label>
              <select v-model="form.categoria_id" class="select select-bordered w-full">
                <option :value="null">Sem categoria</option>
                <option v-for="cat in categoriasFiltradas" :key="cat.id" :value="cat.id">{{ cat.icone }} {{ cat.nome }}</option>
              </select>
              <button type="button" class="btn btn-xs btn-ghost mt-2" @click="abrirModalCategoria">+ Nova categoria</button>
            </div>
            <div v-if="form.tipo === 'saida'">
              <label class="label"><span class="label-text font-semibold">Meta</span></label>
              <select v-model="form.meta_id" class="select select-bordered w-full">
                <option :value="null">Sem meta</option>
                <option v-for="meta in metas.filter((m) => !m.concluida)" :key="meta.id" :value="meta.id">{{ meta.nome }}</option>
              </select>
            </div>
          </div>

          <div class="divider">Encargos</div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="label"><span class="label-text">Multa</span></label>
              <input v-model.number="form.valor_multa" type="number" min="0" step="0.01" class="input input-bordered w-full" />
            </div>
            <div>
              <label class="label"><span class="label-text">Juros</span></label>
              <input v-model.number="form.valor_juros" type="number" min="0" step="0.01" class="input input-bordered w-full" />
            </div>
            <div>
              <label class="label"><span class="label-text">Desconto</span></label>
              <input v-model.number="form.valor_desconto" type="number" min="0" step="0.01" class="input input-bordered w-full" />
            </div>
          </div>

          <div v-if="modoCristao && form.tipo === 'entrada'" class="divider">Dizimo</div>
          <div v-if="modoCristao && form.tipo === 'entrada'" class="flex items-center gap-4">
            <input v-model="form.tem_dizimo" type="checkbox" class="checkbox" />
            <span>Gerar dizimo automatico</span>
            <input v-if="form.tem_dizimo" v-model.number="form.percentual_dizimo" type="number" min="0" max="100" step="0.1" class="input input-bordered w-28" />
            <span v-if="form.tem_dizimo">{{ formatarMoeda(valorDizimo) }}</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label class="flex items-center gap-2"><input v-model="form.fixa" type="checkbox" class="checkbox" /> Fixa</label>
            <label class="flex items-center gap-2"><input v-model="form.recorrente" type="checkbox" class="checkbox" /> Recorrente</label>
            <label class="flex items-center gap-2"><input v-model="form.parcelado" type="checkbox" class="checkbox" /> Parcelado</label>
            <label class="flex items-center gap-2"><input v-model="form.e_emprestimo" type="checkbox" class="checkbox" /> Emprestimo</label>
          </div>

          <div v-if="form.parcelado">
            <label class="label"><span class="label-text">Total de parcelas</span></label>
            <input v-model.number="form.total_parcelas" type="number" min="2" max="48" class="input input-bordered w-full" />
            <p v-if="form.total_parcelas" class="text-sm mt-2">Valor por parcela: {{ formatarMoeda(valorParcela) }}</p>
            <p v-if="form.total_parcelas" class="text-sm mt-1">Total da compra: {{ formatarMoeda(valorTotalParcelado) }}</p>
          </div>

          <div v-if="form.e_emprestimo">
            <label class="label"><span class="label-text">Pessoa</span></label>
            <input v-model="form.pessoa_emprestimo" class="input input-bordered w-full" />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <textarea v-model="form.observacoes" class="textarea textarea-bordered w-full" rows="2" placeholder="Observacoes"></textarea>
            <input v-model="form.tags" class="input input-bordered w-full" placeholder="Tags" />
          </div>

          <div class="alert">
            <span>Valor efetivo: <strong>{{ formatarMoeda(valorEfetivo) }}</strong></span>
          </div>

          <div class="card-actions justify-end border-t pt-4">
            <button type="button" @click="cancelar" class="btn btn-ghost" :disabled="loading">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="!formValido || loading">{{ loading ? 'Salvando...' : 'Salvar' }}</button>
          </div>
        </div>
      </form>
    </div>
  </div>

  <div v-if="showCategoriaModal" class="modal modal-open">
    <div class="modal-box">
      <h3 class="font-bold text-lg mb-4">Nova Categoria</h3>
      <div class="space-y-3">
        <div>
          <label class="label"><span class="label-text">Nome</span></label>
          <input v-model="formCategoria.nome" class="input input-bordered w-full" placeholder="Ex: Feira, Bonus, Farmacia" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label"><span class="label-text">Icone</span></label>
            <input v-model="formCategoria.icone" class="input input-bordered w-full" />
          </div>
          <div>
            <label class="label"><span class="label-text">Cor</span></label>
            <input v-model="formCategoria.cor" type="color" class="input input-bordered w-full p-1 h-11" />
          </div>
        </div>
        <p class="text-xs text-gray-500">Tipo da categoria: {{ form.tipo }}</p>
        <p v-if="erroCategoria" class="text-sm text-error">{{ erroCategoria }}</p>
      </div>
      <div class="modal-action">
        <button class="btn btn-ghost" type="button" @click="fecharModalCategoria" :disabled="criandoCategoria">Cancelar</button>
        <button class="btn btn-primary" type="button" @click="salvarCategoria" :disabled="criandoCategoria || !formCategoria.nome.trim()">
          {{ criandoCategoria ? 'Salvando...' : 'Salvar categoria' }}
        </button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button @click="fecharModalCategoria">close</button>
    </form>
  </div>
</template>

