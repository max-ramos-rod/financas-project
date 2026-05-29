export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  nome: string
  role: 'user'
}

export interface AuthTokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface User {
  id: number
  email: string
  nome: string
  role: string
  avatar_url?: string | null
}
