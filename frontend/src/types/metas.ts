export interface Meta {
  id: number
  user_id: number
  nome: string
  descricao?: string
  valor_alvo: number
  valor_atual: number
  data_inicio: string
  data_fim?: string
  concluida: boolean
  cor: string
  created_at: string
}
