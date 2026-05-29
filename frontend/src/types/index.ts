export type { LoginCredentials, RegisterData, AuthTokenResponse, User } from './auth'
export type { Conta } from './contas'
export type { Categoria } from './categorias'
export type { Transacao } from './transacoes'
export type { Meta } from './metas'
export type { Orcamento } from './orcamentos'
export type { FaturaItem, FaturaResumo } from './fatura'
export type { ImportacaoDuplicata, ImportacaoErro, ImportacaoResult } from './importacao'
export type {
  DelegacaoContextOption,
  Delegacao,
  DelegacaoInviteResponse,
  DelegacaoInviteTokenInfo,
} from './delegacao'
export type { DRECategoriaResumo, DREMensal } from './relatorios'

export interface ApiError {
  detail: string | { loc: string[]; msg: string; type: string }[]
}
