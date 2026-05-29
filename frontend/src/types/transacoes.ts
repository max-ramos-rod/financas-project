export interface Transacao {
  id: number
  item_tipo?: 'transacao' | 'fatura_cartao'
  conta_id: number
  categoria_id: number | null
  descricao: string
  valor: number
  tipo: 'entrada' | 'saida' | 'transferencia'
  data: string
  data_vencimento?: string | null
  data_liquidacao?: string | null
  status_liquidacao?: 'previsto' | 'liquidado' | 'atrasado' | 'cancelado'
  fixa: boolean
  recorrente: boolean
  confirmada?: boolean
  tem_dizimo: boolean
  percentual_dizimo: number
  e_dizimo: boolean
  e_emprestimo?: boolean
  pessoa_emprestimo?: string
  observacoes?: string
  tags?: string
  valor_multa?: number
  valor_juros?: number
  valor_desconto?: number
  meta_id?: number | null
  parcelado: boolean
  parcela_atual?: number
  total_parcelas?: number
  fatura_conta_id?: number | null
  fatura_competencia_ano?: number | null
  fatura_competencia_mes?: number | null
  fatura_periodo_inicio?: string | null
  fatura_periodo_fim?: string | null
  fatura_total_itens?: number | null
}
