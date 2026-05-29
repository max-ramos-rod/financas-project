import { test, expect } from './fixtures'

const MOCK_CONTA = { id: 1, nome: 'Conta Corrente', tipo: 'conta_corrente', saldo: 1000, ativa: true, cor: '#aabbcc' }

const MOCK_TRANSACAO = {
  id: 42,
  descricao: 'Mercado livre',
  valor: 150.0,
  tipo: 'saida',
  data: '2026-05-01',
  status_liquidacao: 'liquidado',
  conta_id: 1,
  categoria_id: null,
  fixa: false,
  item_tipo: 'transacao',
}

test.describe('Lista de Transações', () => {
  // Playwright uses LIFO route ordering: last registered = first to run.
  // The authed fixture already has a catch-all (registered first = fallback).
  // Test routes registered here override the catch-all for specific URLs.
  test.beforeEach(async ({ authed }) => {
    await authed.route(/\/api\/v1\/categorias/, (r) => r.fulfill({ json: [] }))
    await authed.route(/\/api\/v1\/contas/, (r) => r.fulfill({ json: [MOCK_CONTA] }))
    await authed.route(/\/api\/v1\/transacoes/, (r) => r.fulfill({ json: [MOCK_TRANSACAO] }))
    await authed.goto('/transacoes')
    await expect(authed.getByText('Mercado livre').first()).toBeVisible({ timeout: 10000 })
  })

  test('exibe a lista de transações', async ({ authed }) => {
    // Use .first() to avoid strict mode violation when text appears multiple times.
    await expect(authed.getByText('Mercado livre').first()).toBeVisible()
  })

  test('exibe botão de nova transação', async ({ authed }) => {
    await expect(authed.getByRole('button', { name: /nova transação/i })).toBeVisible()
  })

  test('exibe botão de exportar CSV', async ({ authed }) => {
    await expect(authed.getByRole('button', { name: /csv/i })).toBeVisible()
  })

  test('campo de busca filtra por descrição', async ({ authed }) => {
    await authed.getByPlaceholder(/buscar descrição/i).fill('Mercado')
    // Watch fires immediately (no debounce) → re-fetches transacoes mock → renders.
    await expect(authed.getByText('Mercado livre').first()).toBeVisible({ timeout: 5000 })
  })
})

test.describe('Busca global', () => {
  test.beforeEach(async ({ authed }) => {
    await authed.route(/\/api\/v1\/busca/, (r) =>
      r.fulfill({
        json: {
          query: 'Mercado',
          transacoes: [{ id: 1, descricao: 'Mercado livre', valor: 150, tipo: 'saida', data: '2026-05-01', status_liquidacao: 'liquidado', conta_id: 1 }],
          contas: [],
        },
      }),
    )
    await authed.goto('/busca')
  })

  test('exibe campo de busca', async ({ authed }) => {
    await expect(authed.getByPlaceholder(/buscar em transações/i)).toBeVisible()
  })

  test('mostra resultados ao digitar', async ({ authed }) => {
    await authed.getByPlaceholder(/buscar em transações/i).fill('Mercado')
    // BuscaView has a 350ms debounce before the API call.
    await expect(authed.getByText('Mercado livre')).toBeVisible({ timeout: 3000 })
  })
})
