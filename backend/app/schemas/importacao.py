from datetime import date
from typing import List

from pydantic import BaseModel


class ImportacaoDuplicata(BaseModel):
    descricao: str
    valor: float
    tipo: str
    data: date


class ImportacaoErro(BaseModel):
    indice: int
    descricao: str
    motivo: str


class ImportacaoResult(BaseModel):
    formato_detectado: str
    total_no_arquivo: int
    importadas: int
    duplicatas: List[ImportacaoDuplicata]
    erros: List[ImportacaoErro]
