import { describe, expect, it, vi } from 'vitest'
import { TransacoesLoadControl } from './transacoesLoadControl'

describe('TransacoesLoadControl', () => {
  it('faz apenas 1 carga de transacoes no init', async () => {
    const control = new TransacoesLoadControl()
    const aplicarFiltrosDaQuery = vi.fn()
    const fetchApoio = vi.fn().mockResolvedValue(undefined)
    const fetchTransacoes = vi.fn().mockResolvedValue(undefined)

    await control.inicializar({
      aplicarFiltrosDaQuery,
      fetchApoio,
      fetchTransacoes,
    })

    expect(aplicarFiltrosDaQuery).toHaveBeenCalledTimes(1)
    expect(fetchApoio).toHaveBeenCalledTimes(1)
    expect(fetchTransacoes).toHaveBeenCalledTimes(1)
  })

  it('nao dispara busca ao alterar filtros antes da hidratacao', async () => {
    const control = new TransacoesLoadControl()
    const replaceQuery = vi.fn().mockResolvedValue(undefined)
    const fetchTransacoes = vi.fn().mockResolvedValue(undefined)

    await control.aoAlterarFiltros({
      replaceQuery,
      fetchTransacoes,
    })

    expect(replaceQuery).not.toHaveBeenCalled()
    expect(fetchTransacoes).not.toHaveBeenCalled()
  })

  it('dispara 1 replace e 1 busca por alteracao apos hidratacao', async () => {
    const control = new TransacoesLoadControl()
    await control.inicializar({
      aplicarFiltrosDaQuery: vi.fn(),
      fetchApoio: vi.fn().mockResolvedValue(undefined),
      fetchTransacoes: vi.fn().mockResolvedValue(undefined),
    })

    const replaceQuery = vi.fn().mockResolvedValue(undefined)
    const fetchTransacoes = vi.fn().mockResolvedValue(undefined)

    await control.aoAlterarFiltros({
      replaceQuery,
      fetchTransacoes,
    })

    expect(replaceQuery).toHaveBeenCalledTimes(1)
    expect(fetchTransacoes).toHaveBeenCalledTimes(1)
  })
})

