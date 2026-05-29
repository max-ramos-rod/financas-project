export interface ImportacaoDuplicata {
  descricao: string
  valor: number
  tipo: string
  data: string
}

export interface ImportacaoErro {
  indice: number
  descricao: string
  motivo: string
}

export interface ImportacaoResult {
  formato_detectado: string
  total_no_arquivo: number
  importadas: number
  duplicatas: ImportacaoDuplicata[]
  erros: ImportacaoErro[]
}
