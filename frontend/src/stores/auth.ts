import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import api from '@/services/api'
import type { AuthTokenResponse, LoginCredentials, RegisterData, User } from '@/types'

const ACCESS_TOKEN_KEY = 'access_token'
const ACCESS_TOKEN_EXPIRES_AT_KEY = 'access_token_expires_at'
const SESSION_TIMEOUT_SECONDS_KEY = 'session_timeout_seconds'
const LAST_ACTIVITY_AT_KEY = 'last_activity_at'
const ACTIVITY_THROTTLE_MS = 15000
const SESSION_CHECK_INTERVAL_MS = 30000
const DEFAULT_TIMEOUT_SECONDS = 30 * 60

const activityEvents = ['click', 'keydown', 'mousedown', 'scroll', 'touchstart'] as const

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem(ACCESS_TOKEN_KEY))
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sessionExpiresAt = ref<number | null>(Number(localStorage.getItem(ACCESS_TOKEN_EXPIRES_AT_KEY)) || null)
  const sessionTimeoutSeconds = ref<number>(Number(localStorage.getItem(SESSION_TIMEOUT_SECONDS_KEY)) || DEFAULT_TIMEOUT_SECONDS)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isUser = computed(() => user.value?.role === 'user')

  let sessionIntervalId: number | null = null
  let listenersStarted = false
  let lastActivityWriteAt = 0
  let refreshPromise: Promise<boolean> | null = null

  const decodeJwtExpiresAt = (jwtToken: string): number | null => {
    try {
      const [, payloadBase64] = jwtToken.split('.')
      if (!payloadBase64) return null

      const base64 = payloadBase64.replace(/-/g, '+').replace(/_/g, '/')
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')
      const payload = JSON.parse(window.atob(padded)) as { exp?: number }

      return payload.exp ? payload.exp * 1000 : null
    } catch {
      return null
    }
  }

  const persistToken = (payload: AuthTokenResponse) => {
    const expiresAt = Date.now() + payload.expires_in * 1000

    token.value = payload.access_token
    sessionExpiresAt.value = expiresAt
    sessionTimeoutSeconds.value = payload.expires_in

    localStorage.setItem(ACCESS_TOKEN_KEY, payload.access_token)
    localStorage.setItem(ACCESS_TOKEN_EXPIRES_AT_KEY, String(expiresAt))
    localStorage.setItem(SESSION_TIMEOUT_SECONDS_KEY, String(payload.expires_in))

    markActivity(true)
  }

  const syncSessionFromStorage = () => {
    token.value = localStorage.getItem(ACCESS_TOKEN_KEY)

    if (!token.value) {
      sessionExpiresAt.value = null
      return
    }

    const storedExpiresAt = Number(localStorage.getItem(ACCESS_TOKEN_EXPIRES_AT_KEY))
    sessionExpiresAt.value = Number.isFinite(storedExpiresAt) && storedExpiresAt > 0
      ? storedExpiresAt
      : decodeJwtExpiresAt(token.value)

    if (sessionExpiresAt.value) {
      localStorage.setItem(ACCESS_TOKEN_EXPIRES_AT_KEY, String(sessionExpiresAt.value))
    }

    const storedTimeout = Number(localStorage.getItem(SESSION_TIMEOUT_SECONDS_KEY))
    sessionTimeoutSeconds.value = Number.isFinite(storedTimeout) && storedTimeout > 0
      ? storedTimeout
      : DEFAULT_TIMEOUT_SECONDS
    localStorage.setItem(SESSION_TIMEOUT_SECONDS_KEY, String(sessionTimeoutSeconds.value))

    if (!localStorage.getItem(LAST_ACTIVITY_AT_KEY)) {
      localStorage.setItem(LAST_ACTIVITY_AT_KEY, String(Date.now()))
    }
  }

  const clearSessionStorage = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(ACCESS_TOKEN_EXPIRES_AT_KEY)
    localStorage.removeItem(SESSION_TIMEOUT_SECONDS_KEY)
    localStorage.removeItem(LAST_ACTIVITY_AT_KEY)
    localStorage.removeItem('act_as_user_id')
  }

  const redirectToLogin = () => {
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  const handleSessionExpired = () => {
    logout()
    redirectToLogin()
  }

  function markActivity(force = false) {
    if (!token.value) return

    const now = Date.now()
    if (!force && now - lastActivityWriteAt < ACTIVITY_THROTTLE_MS) {
      return
    }

    lastActivityWriteAt = now
    localStorage.setItem(LAST_ACTIVITY_AT_KEY, String(now))
  }

  async function refreshSession() {
    if (!token.value) return false
    if (refreshPromise) return refreshPromise

    refreshPromise = (async () => {
      try {
        const response = await api.post<AuthTokenResponse>('/auth/refresh-session')
        persistToken(response.data)
        return true
      } catch {
        logout()
        return false
      } finally {
        refreshPromise = null
      }
    })()

    return refreshPromise
  }

  const evaluateSession = async () => {
    if (!token.value) return

    const now = Date.now()
    const timeoutMs = sessionTimeoutSeconds.value * 1000
    const expiresAt = sessionExpiresAt.value ?? 0
    const lastActivityAt = Number(localStorage.getItem(LAST_ACTIVITY_AT_KEY) || now)

    if (now - lastActivityAt >= timeoutMs) {
      handleSessionExpired()
      return
    }

    if (expiresAt && now >= expiresAt) {
      handleSessionExpired()
      return
    }

    const refreshThresholdMs = Math.min(timeoutMs / 3, 5 * 60 * 1000)
    if (expiresAt && expiresAt - now <= refreshThresholdMs) {
      await refreshSession()
    }
  }

  const startSessionMonitoring = () => {
    if (typeof window === 'undefined') return
    syncSessionFromStorage()

    if (!listenersStarted) {
      const activityHandler = () => markActivity()
      activityEvents.forEach((eventName) => window.addEventListener(eventName, activityHandler, { passive: true }))
      listenersStarted = true
    }

    if (sessionIntervalId !== null) return

    sessionIntervalId = window.setInterval(() => {
      void evaluateSession()
    }, SESSION_CHECK_INTERVAL_MS)
  }

  async function login(credentials: LoginCredentials) {
    loading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('username', credentials.email)
      formData.append('password', credentials.password)

      const response = await api.post<AuthTokenResponse>('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      persistToken(response.data)
      startSessionMonitoring()
      await fetchUser()

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erro ao fazer login'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterData) {
    loading.value = true
    error.value = null

    try {
      await api.post('/auth/register', data)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Erro ao registrar'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchUser() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      markActivity(true)
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    sessionExpiresAt.value = null
    clearSessionStorage()
  }

  function initializeSessionMonitoring() {
    startSessionMonitoring()
    void evaluateSession()
  }

  if (token.value) {
    startSessionMonitoring()
    void fetchUser()
  }

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    isUser,
    login,
    register,
    logout,
    fetchUser,
    refreshSession,
    initializeSessionMonitoring,
    markActivity,
  }
})
