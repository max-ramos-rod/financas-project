<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { storage } from '@/services/storage'
import type { Conta, ImportacaoResult } from '@/types'

const router = useRouter()

const contas = ref<Conta[]>([])
const contaId = ref<number | null>(null)
const arquivo = ref<File | null>(null)
const loading = ref(false)
const hashingArquivo = ref(false)
const resultado = ref<ImportacaoResult | null>(null)
const erro = ref('')
const mostrarErros = ref(false)
const avisoReimport = ref<{ filename: string; importedAt: string; count: number } | null>(null)

const FORMATOS_ACEITOS = '.ofx,.qfx,.xlsx,.xls,.txt,.ret,.rem,.cnab'

interface HistoricoImport {
  hash: string
  filename: string
  importedAt: string
  count: number
}

const lerHistorico = (): HistoricoImport[] => {
  return storage.getImportHistory() as unknown as HistoricoImport[]
}

const salvarNoHistorico = (hash: string, filename: string, count: number) => {
  const historico = lerHistorico()
  const existente = historico.findIndex(r => r.hash === hash)
  const registro: HistoricoImport = { hash, filename, importedAt: new Date().toISOString(), count }
  if (existente >= 0) {
    historico[existente] = registro
  } else {
    historico.unshift(registro)
    if (historico.length > 50) historico.length = 50
  }
  storage.setImportHistory(historico as unknown as string[])
}

const hashArquivo = async (file: File): Promise<string> => {
  const buffer = await file.arrayBuffer()
  const digest = await crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(digest))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}

const formatarDataHora = (iso: string): string => {
  const d = new Date(iso)
  return d.toLocaleDateString('pt-BR') + ' às ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  const res = await api.get<Conta[]>('/contas')
  contas.value = (res.data as any).items ?? res.data
})

const onArquivo = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  arquivo.value = file
  resultado.value = null
  erro.value = ''
  avisoReimport.value = null

  if (!file) return

  hashingArquivo.value = true
  try {
    const hash = await hashArquivo(file)
    const historico = lerHistorico()
    const encontrado = historico.find(r => r.hash === hash)
    if (encontrado) {
      avisoReimport.value = encontrado
    }
  } finally {
    hashingArquivo.value = false
  }
}

const importar = async () => {
  if (!contaId.value || !arquivo.value) return
  loading.value = true
  erro.value = ''
  resultado.value = null

  const form = new FormData()
  form.append('conta_id', String(contaId.value))
  form.append('file', arquivo.value)

  try {
    const res = await api.post<ImportacaoResult>('/importacao/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    resultado.value = res.data
    mostrarErros.value = false

    if (res.data.importadas > 0) {
      const hash = await hashArquivo(arquivo.value)
      salvarNoHistorico(hash, arquivo.value.name, res.data.importadas)
      avisoReimport.value = null
    }
  } catch (err: any) {
    erro.value = err.response?.data?.detail ?? 'Erro ao importar arquivo.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-base-200">
    <div class="container mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8 max-w-2xl">

      <!-- Header inline -->
      <div class="flex items-center gap-3 mb-6">
        <button class="btn btn-ghost btn-sm gap-1" @click="router.push({ name: 'transacoes' })">
          ← Voltar
        </button>
        <div>
          <h1 class="text-2xl font-semibold tracking-tight">Importar transações</h1>
          <p class="text-xs text-base-content/50 mt-0.5">OFX/QFX · XLSX · CNAB 240</p>
        </div>
      </div>

      <!-- Formulário -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body gap-5">

          <div v-if="erro" class="alert alert-error">
            <span>{{ erro }}</span>
          </div>

          <!-- Conta -->
          <div class="form-control">
            <label class="label py-0 pb-1.5">
              <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/60">Conta de destino</span>
            </label>
            <select v-model="contaId" class="select select-bordered">
              <option :value="null" disabled>Selecione a conta</option>
              <option v-for="c in contas" :key="c.id" :value="c.id">{{ c.nome }}</option>
            </select>
          </div>

          <!-- Arquivo -->
          <div class="form-control">
            <label class="label py-0 pb-1.5">
              <span class="label-text text-[11px] font-mono uppercase tracking-widest text-base-content/60">
                Arquivo
                <span v-if="hashingArquivo" class="loading loading-spinner loading-xs ml-1"></span>
              </span>
            </label>
            <input
              type="file"
              class="file-input file-input-bordered w-full"
              :accept="FORMATOS_ACEITOS"
              @change="onArquivo"
            />
            <label class="label py-0 pt-1">
              <span class="label-text-alt text-base-content/40">Formatos suportados: OFX, QFX, XLSX, CNAB 240</span>
            </label>
          </div>

          <!-- Aviso de re-importação -->
          <div v-if="avisoReimport" class="alert alert-warning py-3 flex-col items-start gap-1">
            <p class="font-semibold text-sm">Este arquivo já foi importado antes.</p>
            <p class="text-xs">
              <span class="font-medium">{{ avisoReimport.filename }}</span>
              foi importado em {{ formatarDataHora(avisoReimport.importedAt) }}
              ({{ avisoReimport.count }} transaç{{ avisoReimport.count === 1 ? 'ão' : 'ões' }}).
              Importar novamente vai duplicar essas transações.
            </p>
          </div>

          <button
            class="btn w-full"
            :class="avisoReimport ? 'btn-warning' : 'btn-primary'"
            :disabled="!contaId || !arquivo || loading || hashingArquivo"
            @click="importar"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            <span v-else-if="avisoReimport">Importar mesmo assim</span>
            <span v-else>Importar</span>
          </button>

        </div>
      </div>

      <!-- Resultado -->
      <template v-if="resultado">

        <!-- Resumo -->
        <div class="card bg-base-100 shadow-sm mt-4">
          <div class="card-body gap-3">
            <div class="flex items-center justify-between">
              <h2 class="font-semibold text-base-content">Resultado da importação</h2>
              <span class="badge badge-ghost text-[11px] font-mono">{{ resultado.formato_detectado }}</span>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div class="stat bg-base-200 rounded-xl p-3">
                <div class="stat-title text-[10px]">No arquivo</div>
                <div class="stat-value text-lg">{{ resultado.total_no_arquivo }}</div>
              </div>
              <div class="stat bg-success/10 rounded-xl p-3">
                <div class="stat-title text-[10px]">Importadas</div>
                <div class="stat-value text-lg text-success">{{ resultado.importadas }}</div>
              </div>
              <div class="stat rounded-xl p-3" :class="resultado.erros.length ? 'bg-error/10' : 'bg-base-200'">
                <div class="stat-title text-[10px]">Erros</div>
                <div class="stat-value text-lg" :class="resultado.erros.length ? 'text-error' : ''">
                  {{ resultado.erros.length }}
                </div>
              </div>
            </div>

            <div v-if="resultado.importadas > 0" class="alert alert-success py-2">
              <span class="text-sm">{{ resultado.importadas }} transaç{{ resultado.importadas === 1 ? 'ão importada' : 'ões importadas' }} com sucesso.</span>
            </div>
          </div>
        </div>

        <!-- Erros de parsing -->
        <div v-if="resultado.erros.length" class="card bg-base-100 shadow-sm mt-4">
          <div class="card-body gap-3 p-4">
            <button
              class="flex items-center justify-between w-full text-left"
              @click="mostrarErros = !mostrarErros"
            >
              <span class="font-medium text-error text-sm">
                {{ resultado.erros.length }} erro{{ resultado.erros.length === 1 ? '' : 's' }} ao processar
              </span>
              <span class="text-base-content/40 text-xs">{{ mostrarErros ? '▲ ocultar' : '▼ ver' }}</span>
            </button>

            <div v-if="mostrarErros" class="space-y-2">
              <div v-for="e in resultado.erros" :key="e.indice" class="rounded-lg bg-error/10 p-3 text-sm">
                <p class="font-medium text-error">{{ e.descricao || `Linha ${e.indice + 1}` }}</p>
                <p class="text-base-content/60 mt-0.5 text-xs">{{ e.motivo }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Ir para transações -->
        <div class="mt-4 flex justify-end">
          <button class="btn btn-ghost btn-sm" @click="router.push({ name: 'transacoes' })">
            Ver transações →
          </button>
        </div>

      </template>
    </div>
  </div>
</template>
