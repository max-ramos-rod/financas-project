import { describe, expect, it } from 'vitest'
import { extractApiError } from '@/services/apiError'

describe('extractApiError', () => {
  it('retorna fallback para null', () => {
    expect(extractApiError(null)).toBe('Ocorreu um erro. Tente novamente.')
  })

  it('retorna fallback para undefined', () => {
    expect(extractApiError(undefined)).toBe('Ocorreu um erro. Tente novamente.')
  })

  it('retorna fallback customizado', () => {
    expect(extractApiError(null, 'Erro customizado.')).toBe('Erro customizado.')
  })

  it('retorna fallback quando não há response', () => {
    expect(extractApiError(new Error('Network Error'))).toBe('Ocorreu um erro. Tente novamente.')
  })

  it('extrai string do detail', () => {
    const err = { response: { data: { detail: 'E-mail já cadastrado.' } } }
    expect(extractApiError(err)).toBe('E-mail já cadastrado.')
  })

  it('retorna fallback para detail string vazia', () => {
    const err = { response: { data: { detail: '   ' } } }
    expect(extractApiError(err)).toBe('Ocorreu um erro. Tente novamente.')
  })

  it('extrai array de strings do detail', () => {
    const err = { response: { data: { detail: ['Campo obrigatório.', 'Valor inválido.'] } } }
    expect(extractApiError(err)).toBe('Campo obrigatório.; Valor inválido.')
  })

  it('extrai array de objetos Pydantic do detail', () => {
    const err = {
      response: {
        data: {
          detail: [
            { loc: ['body', 'email'], msg: 'field required', type: 'value_error.missing' },
            { loc: ['body', 'password'], msg: 'ensure this value has at least 6 characters', type: 'value_error.any_str.min_length' },
          ],
        },
      },
    }
    expect(extractApiError(err)).toBe(
      'field required; ensure this value has at least 6 characters'
    )
  })

  it('extrai objeto com msg do detail', () => {
    const err = { response: { data: { detail: { msg: 'Token expirado.' } } } }
    expect(extractApiError(err)).toBe('Token expirado.')
  })

  it('retorna fallback quando detail é número', () => {
    const err = { response: { data: { detail: 42 } } }
    expect(extractApiError(err)).toBe('Ocorreu um erro. Tente novamente.')
  })

  it('retorna fallback quando data está ausente', () => {
    const err = { response: {} }
    expect(extractApiError(err)).toBe('Ocorreu um erro. Tente novamente.')
  })
})
