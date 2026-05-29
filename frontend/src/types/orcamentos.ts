export interface Orcamento {
  id: number
  user_id: number
  categoria_id: number
  mes: number
  ano: number
  valor_planejado: number
  valor_gasto: number
  created_at: string
}
