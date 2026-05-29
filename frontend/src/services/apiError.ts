export function extractApiError(err: unknown, fallback = 'Ocorreu um erro. Tente novamente.'): string {
  if (!err || typeof err !== 'object') return fallback
  const detail = (err as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const msgs = detail.map((d: unknown) => {
      if (typeof d === 'string') return d
      if (d && typeof d === 'object' && 'msg' in d) return String((d as { msg: unknown }).msg)
      return JSON.stringify(d)
    })
    return msgs.join('; ')
  }
  if (detail && typeof detail === 'object' && 'msg' in detail) return String((detail as { msg: unknown }).msg)
  return fallback
}
