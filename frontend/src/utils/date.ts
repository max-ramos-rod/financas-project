export const parseDate = (dateStr: string) => {
  const [year, month, day] = dateStr.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export const formatDateBR = (dateStr: string) =>
  parseDate(dateStr).toLocaleDateString('pt-BR')
