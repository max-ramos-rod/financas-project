export interface DRECategoriaResumo {
  categoria_id: number | null
  categoria_nome: string
  valor: number
}

export interface DREMensal {
  mes: number
  ano: number
  entradas_liquidadas: number
  entradas_previstas: number
  entradas_total: number
  saidas_liquidadas: number
  saidas_previstas: number
  saidas_total: number
  resultado_liquidado: number
  resultado_previsto: number
  resultado_total: number
  entradas_por_categoria: DRECategoriaResumo[]
  saidas_por_categoria: DRECategoriaResumo[]
}
