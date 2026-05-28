from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class TransacaoImportada:
    descricao: str
    valor: float        # sempre positivo
    tipo: str           # "entrada" | "saida"
    data: date
    observacoes: Optional[str] = None
