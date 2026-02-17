import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()
  const { user, loading, error, isAuthenticated, isUser } = storeToRefs(authStore)
  
  return {
    user,
    loading,
    error,
    isAuthenticated,
    isUser,
    login: authStore.login,
    register: authStore.register,
    logout: authStore.logout
  }
}
