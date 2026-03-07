type InitDeps = {
  aplicarFiltrosDaQuery: () => void
  fetchApoio: () => Promise<void>
  fetchTransacoes: () => Promise<void>
}

type ChangeDeps = {
  replaceQuery: () => Promise<unknown>
  fetchTransacoes: () => Promise<void>
}

export class TransacoesLoadControl {
  private hidratado = false

  async inicializar({ aplicarFiltrosDaQuery, fetchApoio, fetchTransacoes }: InitDeps): Promise<void> {
    aplicarFiltrosDaQuery()
    await fetchApoio()
    await fetchTransacoes()
    this.hidratado = true
  }

  async aoAlterarFiltros({ replaceQuery, fetchTransacoes }: ChangeDeps): Promise<void> {
    if (!this.hidratado) return
    await replaceQuery()
    await fetchTransacoes()
  }
}

