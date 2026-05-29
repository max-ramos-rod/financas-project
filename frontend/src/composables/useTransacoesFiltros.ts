import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import type { FiltrosTransacoes } from '@/views/Transacoes/transacoesFetch'

const MESES_ABREV = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

export { MESES_ABREV }

export function filtrosPadrao(): FiltrosTransacoes {
  return {
    tipo: 'todas',
    status_liquidacao: 'todos',
    fixa: 'todas',
    orcamento: 'todos',
    valor_modo: 'todos',
    valor_ref: '',
    conta_id: null,
    categoria_id: null,
    mes: new Date().getMonth() + 1,
    ano: new Date().getFullYear(),
    busca: '',
  }
}

function parseNumberQuery(value: unknown): number | null {
  if (typeof value !== 'string' || value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

export function useTransacoesFiltros() {
  const route = useRoute()

  const filtros = ref<FiltrosTransacoes>(filtrosPadrao())

  const labelPeriodoAtual = computed(() => {
    const m = filtros.value.mes
    const a = filtros.value.ano
    if (!m) return `${a}`
    return `${MESES_ABREV[m - 1]} ${a}`
  })

  const temFiltrosAtivos = computed(() => {
    const f = filtros.value
    const d = filtrosPadrao()
    return (
      f.tipo !== d.tipo ||
      f.status_liquidacao !== d.status_liquidacao ||
      f.busca !== d.busca ||
      f.conta_id !== d.conta_id ||
      f.categoria_id !== d.categoria_id ||
      f.fixa !== d.fixa ||
      f.orcamento !== d.orcamento
    )
  })

  const aplicarFiltrosDaQuery = () => {
    const q = route.query
    const anoAtual = new Date().getFullYear()
    const mesAtual = new Date().getMonth() + 1
    filtros.value = {
      tipo: q.tipo === 'entrada' || q.tipo === 'saida' ? q.tipo : 'todas',
      status_liquidacao:
        q.status_liquidacao === 'previsto' ||
        q.status_liquidacao === 'liquidado' ||
        q.status_liquidacao === 'atrasado' ||
        q.status_liquidacao === 'cancelado'
          ? q.status_liquidacao
          : 'todos',
      fixa: q.fixa === 'fixas' || q.fixa === 'nao_fixas' ? q.fixa : 'todas',
      orcamento: q.orcamento === 'fora' || q.orcamento === 'dentro' ? q.orcamento : 'todos',
      valor_modo:
        q.valor_modo === 'igual' || q.valor_modo === 'gte' || q.valor_modo === 'lte'
          ? q.valor_modo
          : 'todos',
      valor_ref: typeof q.valor_ref === 'string' ? q.valor_ref : '',
      conta_id: parseNumberQuery(q.conta_id),
      categoria_id: parseNumberQuery(q.categoria_id),
      mes: parseNumberQuery(q.mes) ?? mesAtual,
      ano: parseNumberQuery(q.ano) ?? anoAtual,
      busca: typeof q.busca === 'string' ? q.busca : '',
    }
  }

  const queryAtualDosFiltros = () => ({
    tipo: filtros.value.tipo,
    status_liquidacao: filtros.value.status_liquidacao,
    fixa: filtros.value.fixa !== 'todas' ? filtros.value.fixa : undefined,
    orcamento: filtros.value.orcamento !== 'todos' ? filtros.value.orcamento : undefined,
    valor_modo: filtros.value.valor_modo !== 'todos' ? filtros.value.valor_modo : undefined,
    valor_ref: filtros.value.valor_ref.trim() || undefined,
    conta_id: filtros.value.conta_id != null ? String(filtros.value.conta_id) : undefined,
    categoria_id:
      filtros.value.categoria_id != null ? String(filtros.value.categoria_id) : undefined,
    mes: filtros.value.mes != null ? String(filtros.value.mes) : undefined,
    ano: filtros.value.ano ? String(filtros.value.ano) : undefined,
    busca: filtros.value.busca || undefined,
  })

  const limparFiltros = () => {
    filtros.value = filtrosPadrao()
  }

  const setTipoAba = (tipo: 'todas' | 'entrada' | 'saida') => {
    filtros.value.tipo = tipo
  }

  return {
    filtros,
    labelPeriodoAtual,
    temFiltrosAtivos,
    aplicarFiltrosDaQuery,
    queryAtualDosFiltros,
    limparFiltros,
    setTipoAba,
  }
}
