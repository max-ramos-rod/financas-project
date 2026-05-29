import type { User } from './auth'

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
