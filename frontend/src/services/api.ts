import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type { ApiError } from '@/types'

//const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';
const API_URL = '/api/v1';

class ApiService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
        'bypass-tunnel-reminder': 'true', // ✅ Isso bypassa a página de verificação
      },
    })

    // Request interceptor - adiciona token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        const actAsUser = localStorage.getItem('act_as_user_id')
        if (actAsUser) {
          config.headers['X-Act-As-User'] = actAsUser
        }

        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - trata erros
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('act_as_user_id')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  get instance() {
    return this.api
  }
}

export const api = new ApiService().instance
export default api
