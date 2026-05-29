export function valorEfetivo(t: {
  valor: number
  valor_multa?: number | null
  valor_juros?: number | null
  valor_desconto?: number | null
}): number {
  return Math.max(
    0,
    (t.valor || 0) + (t.valor_multa || 0) + (t.valor_juros || 0) - (t.valor_desconto || 0),
  )
}

export function formatarMoeda(valor: number): string {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor)
}

export function formatarCompacto(valor: number): string {
  if (valor >= 1000) {
    const k = valor / 1000
    return `R$ ${new Intl.NumberFormat('pt-BR', { maximumFractionDigits: k >= 10 ? 0 : 1 }).format(k)}k`
  }
  return formatarMoeda(valor)
}
