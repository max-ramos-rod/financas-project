/**
 * strings.ts · Glossário central PT-BR · Finanças Cristãs
 * ----------------------------------------------------------------------------
 * Inventário em mai/2026: 22 strings PT-BR sem acento espalhadas em 11 arquivos.
 * Esse glossário corrige todas de uma vez e serve como referência para QA visual.
 *
 * Uso:
 *   import { LABELS } from '@/utils/strings'
 *   <h1>{{ LABELS.transacoes }}</h1>
 *
 * Nunca hardcodar strings de domínio nos templates. Aceitável: micro-textos
 * de UI únicos (mensagens de empty state específicos, descrições de campo).
 */

export const LABELS = {
  // === NAVEGAÇÃO PRINCIPAL ===
  dashboard: 'Dashboard',
  transacoes: 'Transações',
  contas: 'Contas',
  busca: 'Busca',
  metas: 'Metas',
  orcamentos: 'Orçamentos',
  categorias: 'Categorias',
  relatorios: 'Relatórios',

  // === GRUPOS DE MENU ===
  gestao: 'Gestão',
  colaboracao: 'Colaboração',

  // === TRANSAÇÕES ===
  entradas: 'Entradas',
  saidas: 'Saídas',
  todas: 'Todas',
  nova_transacao: 'Nova transação',
  editar_transacao: 'Editar transação',

  // === STATUS DE TRANSAÇÃO (e_status_liquidacao) ===
  st_previsto: 'Previsto',
  st_liquidado: 'Liquidado',
  st_atrasado: 'Atrasado',
  st_cancelado: 'Cancelado',
  recebido: 'Recebido',
  pago: 'Pago',
  a_receber: 'A receber',
  a_pagar: 'A pagar',

  // === TIPOS DE CONTA (substitui formatarTipo() com emoji) ===
  conta_carteira: 'Carteira',
  conta_corrente: 'Conta corrente',
  conta_poupanca: 'Poupança',
  conta_cartao: 'Cartão de crédito',
  conta_investimento: 'Investimento',
  conta_outro: 'Outro',

  // === DELEGAÇÕES (substitui status em inglês) ===
  deleg_pending: 'Aguardando',
  deleg_accepted: 'Aceito',
  deleg_revoked: 'Revogado',

  // === KPI / DASHBOARD ===
  saldo_total: 'Saldo total',
  saldo_do_mes: 'Saldo do mês',
  receitas_do_mes: 'Receitas do mês',
  despesas_do_mes: 'Despesas do mês',
  cartao_em_aberto: 'Cartão em aberto',
  resultado_positivo: 'Resultado positivo no período',
  resultado_negativo: 'Atenção ao fluxo do período',
  mes_de_referencia: 'Mês de referência',

  // === MENSAGENS GENÉRICAS ===
  carregando: 'Carregando…',
  salvando: 'Salvando…',
  sem_categoria: 'Sem categoria',
  meu_espaco: 'Meu espaço',
} as const

/**
 * Mapeia o tipo do backend (snake_case) para o label PT-BR canônico.
 * Substitui formatarTipo() em ListaContasView.vue.
 */
export function labelTipoConta(tipo: string): string {
  switch (tipo) {
    case 'carteira': return LABELS.conta_carteira
    case 'conta_corrente': return LABELS.conta_corrente
    case 'poupanca': return LABELS.conta_poupanca
    case 'cartao_credito': return LABELS.conta_cartao
    case 'investimento': return LABELS.conta_investimento
    case 'outro': return LABELS.conta_outro
    default: return tipo
  }
}

/**
 * Mapeia status de delegação para PT-BR.
 */
export function labelStatusDelegacao(status: string): string {
  switch (status) {
    case 'pending': return LABELS.deleg_pending
    case 'accepted': return LABELS.deleg_accepted
    case 'revoked': return LABELS.deleg_revoked
    default: return status
  }
}

/**
 * Cor semântica do status para badges DaisyUI.
 * Use como `badge-${corStatusDelegacao(status)}`.
 */
export function corStatusDelegacao(status: string): 'success' | 'warning' | 'error' | 'ghost' {
  switch (status) {
    case 'accepted': return 'success'
    case 'pending': return 'warning'
    case 'revoked': return 'error'
    default: return 'ghost'
  }
}
