// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest'
import { storage } from '@/services/storage'

beforeEach(() => {
  localStorage.clear()
})

describe('storage — token', () => {
  it('set e get retornam o mesmo valor', () => {
    storage.setToken('abc123')
    expect(storage.getToken()).toBe('abc123')
  })

  it('remove apaga o valor', () => {
    storage.setToken('abc123')
    storage.removeToken()
    expect(storage.getToken()).toBeNull()
  })

  it('get retorna null quando não existe', () => {
    expect(storage.getToken()).toBeNull()
  })
})

describe('storage — tokenExpiresAt', () => {
  it('set e get funcionam', () => {
    storage.setTokenExpiresAt('2026-01-01T00:00:00Z')
    expect(storage.getTokenExpiresAt()).toBe('2026-01-01T00:00:00Z')
  })

  it('remove apaga o valor', () => {
    storage.setTokenExpiresAt('2026-01-01T00:00:00Z')
    storage.removeTokenExpiresAt()
    expect(storage.getTokenExpiresAt()).toBeNull()
  })
})

describe('storage — sessionTimeout', () => {
  it('set e get funcionam', () => {
    storage.setSessionTimeout('3600')
    expect(storage.getSessionTimeout()).toBe('3600')
  })

  it('remove apaga o valor', () => {
    storage.setSessionTimeout('3600')
    storage.removeSessionTimeout()
    expect(storage.getSessionTimeout()).toBeNull()
  })
})

describe('storage — lastActivity', () => {
  it('set e get funcionam', () => {
    storage.setLastActivity('1234567890')
    expect(storage.getLastActivity()).toBe('1234567890')
  })

  it('remove apaga o valor', () => {
    storage.setLastActivity('1234567890')
    storage.removeLastActivity()
    expect(storage.getLastActivity()).toBeNull()
  })
})

describe('storage — importHistory', () => {
  it('retorna array vazio quando não existe', () => {
    expect(storage.getImportHistory()).toEqual([])
  })

  it('set e get preservam o array', () => {
    storage.setImportHistory(['hash1', 'hash2'])
    expect(storage.getImportHistory()).toEqual(['hash1', 'hash2'])
  })

  it('retorna array vazio se valor armazenado for JSON inválido', () => {
    localStorage.setItem('financas_import_history', 'nao-e-json')
    expect(storage.getImportHistory()).toEqual([])
  })
})

describe('storage — clearSession', () => {
  it('remove token, expiresAt, timeout, lastActivity e actAsUser', () => {
    storage.setToken('t')
    storage.setTokenExpiresAt('exp')
    storage.setSessionTimeout('3600')
    storage.setLastActivity('now')

    storage.clearSession()

    expect(storage.getToken()).toBeNull()
    expect(storage.getTokenExpiresAt()).toBeNull()
    expect(storage.getSessionTimeout()).toBeNull()
    expect(storage.getLastActivity()).toBeNull()
    expect(storage.getActAsUser()).toBeNull()
  })

  it('não apaga importHistory', () => {
    storage.setImportHistory(['hash1'])
    storage.clearSession()
    expect(storage.getImportHistory()).toEqual(['hash1'])
  })
})
