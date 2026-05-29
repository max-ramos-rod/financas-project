const KEYS = {
  token: 'access_token',
  tokenExpiresAt: 'access_token_expires_at',
  sessionTimeout: 'session_timeout_seconds',
  lastActivity: 'last_activity_at',
  actAsUser: 'act_as_user_id',
  importHistory: 'financas_import_history',
} as const

type StorageKey = typeof KEYS[keyof typeof KEYS]

function safeGet(key: StorageKey): string | null {
  try { return localStorage.getItem(key) } catch { return null }
}

function safeSet(key: StorageKey, value: string): void {
  try { localStorage.setItem(key, value) } catch { /* ignore */ }
}

function safeRemove(key: StorageKey): void {
  try { localStorage.removeItem(key) } catch { /* ignore */ }
}

export const storage = {
  // Token de sessão
  getToken: () => safeGet(KEYS.token),
  setToken: (v: string) => safeSet(KEYS.token, v),
  removeToken: () => safeRemove(KEYS.token),

  // Expiração
  getTokenExpiresAt: () => safeGet(KEYS.tokenExpiresAt),
  setTokenExpiresAt: (v: string) => safeSet(KEYS.tokenExpiresAt, v),
  removeTokenExpiresAt: () => safeRemove(KEYS.tokenExpiresAt),

  // Timeout de sessão
  getSessionTimeout: () => safeGet(KEYS.sessionTimeout),
  setSessionTimeout: (v: string) => safeSet(KEYS.sessionTimeout, v),
  removeSessionTimeout: () => safeRemove(KEYS.sessionTimeout),

  // Última atividade
  getLastActivity: () => safeGet(KEYS.lastActivity),
  setLastActivity: (v: string) => safeSet(KEYS.lastActivity, v),
  removeLastActivity: () => safeRemove(KEYS.lastActivity),

  // Delegação
  getActAsUser: () => safeGet(KEYS.actAsUser),
  removeActAsUser: () => safeRemove(KEYS.actAsUser),

  // Histórico de importações
  getImportHistory: (): string[] => {
    try { return JSON.parse(safeGet(KEYS.importHistory) ?? '[]') } catch { return [] }
  },
  setImportHistory: (v: string[]) => safeSet(KEYS.importHistory, JSON.stringify(v)),

  // Limpar tudo de sessão
  clearSession: () => {
    safeRemove(KEYS.token)
    safeRemove(KEYS.tokenExpiresAt)
    safeRemove(KEYS.sessionTimeout)
    safeRemove(KEYS.lastActivity)
    safeRemove(KEYS.actAsUser)
  },
}
