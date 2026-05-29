import { test, expect } from './fixtures'

const MOCK_FATURA = {
  conta_id: 6,
  conta_nome: 'Nubank',
  competencia_ano: 2026,
  competencia_mes: 6,
  periodo_inicio: '2026-05-14',
  periodo_fim: '2026-06-13',
  dia_fechamento: 13,
  dia_vencimento: 20,
  data_fechamento_prevista: '2026-06-13',
  data_fechamento_real: null,
  data_fechamento_fatura: '2026-06-13',
  data_vencimento_prevista: '2026-06-20',
  data_vencimento_real: null,
  data_vencimento_fatura: '2026-06-20',
  observacao_ciclo: null,
  total_itens: 2,
  valor_total: 350.0,
  valor_pago: 0.0,
  valor_a_pagar: 350.0,
  itens: [
    { transacao_id: 1, descricao: 'Netflix', data: '2026-05-15', data_vencimento: null, status_liquidacao: 'previsto', tipo: 'saida', valor: 55.0, valor_multa: 0, valor_juros: 0, valor_desconto: 0, valor_efetivo: 55.0 },
    { transacao_id: 2, descricao: 'Supermercado', data: '2026-05-20', data_vencimento: null, status_liquidacao: 'previsto', tipo: 'saida', valor: 295.0, valor_multa: 0, valor_juros: 0, valor_desconto: 0, valor_efetivo: 295.0 },
  ],
}

const MOCK_CONTAS = [
  { id: 6, nome: 'Nubank', tipo: 'cartao_credito', saldo: 0, ativa: true, cor: '#8a2be2', dia_fechamento: 13, dia_vencimento: 20 },
  { id: 2, nome: 'Conta Corrente', tipo: 'conta_corrente', saldo: 5000, ativa: true, cor: '#aabbcc' },
]

test.describe('Fatura do Cartão', () => {
  // LIFO ordering: last registered = first to run.
  // Register from most general to most specific so specific routes win.
  test.beforeEach(async ({ authed }) => {
    await authed.route(/\/api\/v1\/contas$/, (r) => r.fulfill({ json: MOCK_CONTAS }))
    await authed.route(/\/api\/v1\/contas\/6\/faturas\//, (r) => r.fulfill({ json: MOCK_FATURA }))
    await authed.route(/\/api\/v1\/contas\/6\/fatura-atual/, (r) => r.fulfill({ json: MOCK_FATURA }))
    await authed.goto('/contas/6/fatura')
    // Wait for the page to fully load (fatura items visible).
    await expect(authed.getByText('Netflix').first()).toBeVisible({ timeout: 10000 })
  })

  test('exibe o nome do cartão no título', async ({ authed }) => {
    await expect(authed.getByRole('heading', { name: /fatura do cartão/i })).toBeVisible()
  })

  test('exibe itens da fatura', async ({ authed }) => {
    await expect(authed.getByText('Netflix').first()).toBeVisible()
    await expect(authed.getByText('Supermercado').first()).toBeVisible()
  })

  test('exibe botão de exportar PDF', async ({ authed }) => {
    await expect(authed.getByRole('button', { name: /pdf/i })).toBeVisible()
  })

  test('exibe botão de nova transação', async ({ authed }) => {
    await expect(authed.getByRole('button', { name: /nova transação/i })).toBeVisible()
  })

  test('botão voltar navega para /contas', async ({ authed }) => {
    await authed.route(/\/api\/v1\/contas/, (r) => r.fulfill({ json: MOCK_CONTAS }))
    await authed.getByRole('button', { name: /← contas/i }).click()
    await expect(authed).toHaveURL('/contas')
  })
})
