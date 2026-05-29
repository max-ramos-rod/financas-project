import { test as base, type Page } from '@playwright/test'

export const API_RE = /\/api\/v1\//

export const MOCK_USER = {
  id: 1,
  email: 'alice@test.com',
  nome: 'Alice Tester',
  role: 'user',
}

export const MOCK_TOKEN = 'mock-jwt-token'

/** Inject auth state into localStorage before any navigation. */
export async function setAuth(page: Page) {
  const expiresAt = Date.now() + 3600 * 1000
  await page.addInitScript(({ token, ea, now }: { token: string; ea: number; now: number }) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('access_token_expires_at', String(ea))
    localStorage.setItem('session_timeout_seconds', '3600')
    localStorage.setItem('last_activity_at', String(now))
  }, { token: MOCK_TOKEN, ea: expiresAt, now: Date.now() })
}

/**
 * Authenticated test fixture.
 *
 * Route registration order matters: Playwright processes handlers in LIFO
 * (last registered = first to run). We register the catch-all FIRST so it
 * acts as a fallback, then /auth/me LAST so it wins for that specific URL.
 */
export const test = base.extend<{ authed: Page }>({
  authed: async ({ page }, use) => {
    await setAuth(page)
    // Catch-all fallback (registered first → runs last in LIFO).
    // Prevents any non-mocked API call from reaching the real server and
    // returning 401, which would trigger the axios interceptor and clear auth.
    await page.route(API_RE, (r) => r.fulfill({ json: {} }))
    // /auth/me mock (registered last → runs first in LIFO for this URL).
    await page.route(/\/api\/v1\/auth\/me/, (r) => r.fulfill({ json: MOCK_USER }))
    await use(page)
  },
})

export { expect } from '@playwright/test'
