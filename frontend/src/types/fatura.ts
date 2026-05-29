export interface FaturaItem {
  transacao_id: number
  descricao: string
  data: string
  data_vencimento?: string | null
  status_liquidacao: 'previsto' | 'liquidado' | 'atrasado' | 'cancelado'
  tipo: 'saida' | 'entrada'
  valor: number
  valor_multa: number
  valor_juros: number
  valor_desconto: number
  valor_efetivo: number
}

export interface FaturaResumo {
  conta_id: number
  conta_nome: string
  competencia_ano: number
  competencia_mes: number
  periodo_inicio: string
  periodo_fim: string
  dia_fechamento: number
  dia_vencimento: number
  data_fechamento_prevista: string
  data_fechamento_real?: string | null
  data_fechamento_fatura: string
  data_vencimento_prevista: string
  data_vencimento_real?: string | null
  data_vencimento_fatura: string
  observacao_ciclo?: string | null
  total_itens: number
  valor_total: number
  valor_pago: number
  valor_a_pagar: number
  itens: FaturaItem[]
}
