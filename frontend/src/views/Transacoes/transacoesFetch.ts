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

export const montarParamsApiDosFiltros = (filtros: FiltrosTransacoes) => ({
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
})

type ApiClient = {
  get: (url: string, config?: { params?: Record<string, unknown> }) => Promise<{ data: unknown }>
}

export const buscarTransacoesFiltradas = async (
  apiClient: ApiClient,
  filtros: FiltrosTransacoes,
) => {
  const response = await apiClient.get('/transacoes', {
    params: montarParamsApiDosFiltros(filtros),
  })
  return response.data
}

