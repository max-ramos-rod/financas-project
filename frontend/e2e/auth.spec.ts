import { expect, test } from '@playwright/test'

const API = /\/api\/v1\//

test.describe('Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('renders login form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /entrar/i })).toBeVisible()
    await expect(page.getByPlaceholder('você@email.com')).toBeVisible()
    await expect(page.getByRole('button', { name: /^entrar$/i })).toBeVisible()
  })

  test('shows error on invalid credentials', async ({ page }) => {
    // Use 422 instead of 401 — 401 triggers the axios interceptor which
    // clears localStorage and reloads the page before the error can render.
    await page.route(/\/api\/v1\/auth\/login/, (r) =>
      r.fulfill({ status: 422, json: { detail: 'Credenciais inválidas.' } }),
    )
    await page.getByPlaceholder('você@email.com').fill('wrong@test.com')
    await page.getByPlaceholder('••••••••').fill('wrongpass')
    // Use Promise.all to ensure the response is captured before asserting.
    const [response] = await Promise.all([
      page.waitForResponse(/\/api\/v1\/auth\/login/),
      page.getByRole('button', { name: /^entrar$/i }).click(),
    ])
    expect(response.status()).toBe(422)
    await expect(page.getByText(/credenciais inválidas/i)).toBeVisible({ timeout: 8000 })
  })

  test('redirects to dashboard on successful login', async ({ page }) => {
    await page.route(/\/api\/v1\/auth\/login/, (r) =>
      r.fulfill({
        json: { access_token: 'jwt-tok', token_type: 'bearer', expires_in: 3600 },
      }),
    )
    await page.route(/\/api\/v1\/auth\/me/, (r) =>
      r.fulfill({ json: { id: 1, email: 'alice@test.com', nome: 'Alice', role: 'user' } }),
    )
    await page.route(/\/api\/v1\/contas/, (r) => r.fulfill({ json: [] }))
    await page.route(/\/api\/v1\//, (r) => r.fulfill({ json: {} }))

    await page.getByPlaceholder('você@email.com').fill('alice@test.com')
    await page.getByPlaceholder('••••••••').fill('senha123')
    await page.getByRole('button', { name: /^entrar$/i }).click()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('has link to forgot password page', async ({ page }) => {
    await page.getByRole('link', { name: /esqueci/i }).click()
    await expect(page).toHaveURL('/recuperar-senha')
  })
})

test.describe('Recuperação de senha', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recuperar-senha')
  })

  test('renders email form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /esqueci a senha/i })).toBeVisible()
    await expect(page.getByPlaceholder('você@email.com')).toBeVisible()
  })

  test('shows confirmation after submit', async ({ page }) => {
    await page.route(/\/api\/v1\/auth\/forgot-password/, (r) => r.fulfill({ status: 200, json: {} }))
    await page.getByPlaceholder('você@email.com').fill('alice@test.com')
    await page.getByRole('button', { name: /enviar instruções/i }).click()
    await expect(page.getByRole('heading', { name: /verifique seu e-mail/i })).toBeVisible()
  })
})

test.describe('Redefinição de senha', () => {
  test('shows error when no token in URL', async ({ page }) => {
    await page.goto('/redefinir-senha')
    await expect(page.getByText(/link inválido/i)).toBeVisible()
  })

  test('shows form when token is present', async ({ page }) => {
    await page.goto('/redefinir-senha?token=abc123')
    await expect(page.getByRole('heading', { name: /redefinir senha/i })).toBeVisible()
  })

  test('redirects to login after successful reset', async ({ page }) => {
    await page.route(/\/api\/v1\/auth\/reset-password/, (r) => r.fulfill({ status: 200, json: {} }))
    await page.goto('/redefinir-senha?token=validtoken')
    const inputs = page.getByPlaceholder('••••••••')
    await inputs.first().fill('novasenha99')
    await inputs.nth(1).fill('novasenha99')
    await page.getByRole('button', { name: /redefinir senha/i }).click()
    await expect(page).toHaveURL(/\/login/)
  })
})
