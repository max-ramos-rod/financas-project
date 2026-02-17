export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  nome: string
  role: 'user'
}

export interface User {
  id: number
  email: string
  nome: string
  role: string
}

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
}

export interface Categoria {
  id: number
  nome: string
  icone: string
  cor: string
  tipo: string
  padrao: boolean
}

export interface Transacao {
  id: number
  conta_id: number
  categoria_id: number | null
  descricao: string
  valor: number
  tipo: "entrada" | "saida" | "transferencia"
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
}

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

export interface FaturaItem {
  transacao_id: number
  descricao: string
  data: string
  data_vencimento?: string | null
  status_liquidacao: 'previsto' | 'liquidado' | 'atrasado' | 'cancelado'
  valor: number
  valor_multa: number
  valor_juros: number
  valor_desconto: number
  valor_efetivo: number
}

export interface FaturaResumo {
  conta_id: number
  conta_nome: string
  periodo_inicio: string
  periodo_fim: string
  dia_fechamento: number
  dia_vencimento: number
  data_vencimento_fatura: string
  total_itens: number
  valor_total: number
  itens: FaturaItem[]
}
export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[]
}

export interface DelegacaoContextOption {
  user_id: number
  nome: string
  email: string
  can_write: boolean
  is_owner: boolean
}

export interface Delegacao {
  id: number
  owner_user_id: number
  delegate_user_id?: number | null
  invited_email: string
  status: 'pending' | 'active' | 'revoked'
  can_write: boolean
  invite_expires_at?: string | null
  created_at?: string
  accepted_at?: string
  revoked_at?: string
  owner?: User
  delegate?: User | null
}

export interface DelegacaoInviteResponse {
  delegacao: Delegacao
  has_account: boolean
  email_sent: boolean
}

export interface DelegacaoInviteTokenInfo {
  invited_email: string
  owner_nome: string
  owner_email: string
  has_account: boolean
  expired: boolean
}
