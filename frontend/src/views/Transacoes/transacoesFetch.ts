import type { PagedResponse } from '@/types'
import type { Transacao } from '@/types'

export type FiltrosTransacoes = {
  tipo: 'todas' | 'entrada' | 'saida'
  status_liquidacao: 'todos' | 'previsto' | 'liquidado' | 'atrasado' | 'cancelado'
  fixa: 'todas' | 'fixas' | 'nao_fixas'
  orcamento: 'todos' | 'fora' | 'dentro'
  valor_modo: 'todos' | 'igual' | 'gte' | 'lte'
  valor_ref: string
  conta_id: number | null
  categoria_id: number | null
  mes: number | null
  ano: number
  busca: string
}

export const montarParamsApiDosFiltros = (filtros: FiltrosTransacoes, page = 1, page_size = 50) => ({
  tipo: filtros.tipo !== 'todas' ? filtros.tipo : undefined,
  status_liquidacao: filtros.status_liquidacao !== 'todos' ? filtros.status_liquidacao : undefined,
  fixa: filtros.fixa !== 'todas' ? filtros.fixa : undefined,
  orcamento: filtros.orcamento !== 'todos' ? filtros.orcamento : undefined,
  valor_modo: filtros.valor_modo !== 'todos' ? filtros.valor_modo : undefined,
  valor_ref: filtros.valor_ref.trim() || undefined,
  conta_id: filtros.conta_id != null ? filtros.conta_id : undefined,
  categoria_id: filtros.categoria_id != null ? filtros.categoria_id : undefined,
  mes: filtros.mes != null ? filtros.mes : undefined,
  ano: filtros.ano || undefined,
  busca: filtros.busca || undefined,
  page,
  page_size,
})

type ApiClient = {
  get: (url: string, config?: { params?: Record<string, unknown> }) => Promise<{ data: unknown }>
}

export const buscarTransacoesFiltradas = async (
  apiClient: ApiClient,
  filtros: FiltrosTransacoes,
  page = 1,
  page_size = 50,
): Promise<PagedResponse<Transacao>> => {
  const response = await apiClient.get('/transacoes/visao-financeira', {
    params: montarParamsApiDosFiltros(filtros, page, page_size),
  })
  return response.data as PagedResponse<Transacao>
}
