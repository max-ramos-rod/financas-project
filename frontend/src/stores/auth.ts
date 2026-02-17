import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import type { User, LoginCredentials, RegisterData } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isUser = computed(() => user.value?.role === 'user')

  async function login(credentials: LoginCredentials) {
    loading.value = true
    error.value = null
    
    try {
      const formData = new FormData()
      formData.append('username', credentials.email)
      formData.append('password', credentials.password)
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      token.value = response.data.access_token
      localStorage.setItem('access_token', response.data.access_token)
      
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
    } catch (err) {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
  }

  // Carregar usuário ao inicializar se houver token
  if (token.value) {
    fetchUser()
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
    fetchUser
  }
})
