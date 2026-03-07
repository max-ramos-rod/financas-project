import { describe, expect, it, vi } from 'vitest'
import { buscarTransacoesFiltradas, montarParamsApiDosFiltros, type FiltrosTransacoes } from './transacoesFetch'

const filtrosBase: FiltrosTransacoes = {
  tipo: 'todas',
  status_liquidacao: 'todos',
  fixa: 'todas',
  orcamento: 'todos',
  valor_modo: 'todos',
  valor_ref: '',
  conta_id: null,
  categoria_id: null,
  mes: 3,
  ano: 2026,
  busca: '',
}

describe('transacoesFetch', () => {
  it('monta params removendo filtros "todos" e mantendo mes/ano', () => {
    const params = montarParamsApiDosFiltros(filtrosBase)

    expect(params.tipo).toBeUndefined()
    expect(params.status_liquidacao).toBeUndefined()
    expect(params.fixa).toBeUndefined()
    expect(params.orcamento).toBeUndefined()
    expect(params.valor_modo).toBeUndefined()
    expect(params.valor_ref).toBeUndefined()
    expect(params.conta_id).toBeUndefined()
    expect(params.categoria_id).toBeUndefined()
    expect(params.mes).toBe(3)
    expect(params.ano).toBe(2026)
  })

  it('chama api.get uma vez com params filtrados', async () => {
    const apiGet = vi.fn().mockResolvedValue({ data: [{ id: 1 }] })
    const apiClient = { get: apiGet }
    const filtros: FiltrosTransacoes = {
      ...filtrosBase,
      tipo: 'saida',
      fixa: 'nao_fixas',
      orcamento: 'fora',
      valor_modo: 'gte',
      valor_ref: '200,00',
      categoria_id: -1,
      busca: 'mercado',
    }

    const data = await buscarTransacoesFiltradas(apiClient, filtros)

    expect(data).toEqual([{ id: 1 }])
    expect(apiGet).toHaveBeenCalledTimes(1)
    expect(apiGet).toHaveBeenCalledWith('/transacoes', {
      params: {
        tipo: 'saida',
        status_liquidacao: undefined,
        fixa: 'nao_fixas',
        orcamento: 'fora',
        valor_modo: 'gte',
        valor_ref: '200,00',
        conta_id: undefined,
        categoria_id: -1,
        mes: 3,
        ano: 2026,
        busca: 'mercado',
      },
    })
  })
})

