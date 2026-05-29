export interface Conta {
  id: number
  nome: string
  tipo: string
  saldo: number
  dia_fechamento?: number | null
  dia_vencimento?: number | null
  limite_credito?: number | null
  cor: string
  ativa: boolean
  valor_fatura_aberta?: number | null
  valor_fatura_fechada?: number | null
  valor_fatura_fechada_pago?: number | null
  valor_fatura_fechada_total?: number | null
  total_itens_fatura_aberta?: number | null
  total_itens_fatura_fechada?: number | null
  periodo_fatura_inicio?: string | null
  periodo_fatura_fim?: string | null
  periodo_fatura_fechada_inicio?: string | null
  periodo_fatura_fechada_fim?: string | null
  data_fechamento_fatura?: string | null
  data_vencimento_fatura?: string | null
  data_vencimento_fatura_fechada?: string | null
}
