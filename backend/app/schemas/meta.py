from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

class MetaBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    valor_alvo: float
    valor_atual: Optional[float] = 0.0
    data_inicio: date
    data_fim: Optional[date] = None
    concluida: Optional[bool] = False
    cor: Optional[str] = "#10B981"

class MetaCreate(MetaBase):
    pass

class MetaUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    valor_alvo: Optional[float] = None
    valor_atual: Optional[float] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    concluida: Optional[bool] = None
    cor: Optional[str] = None

class MetaResponse(MetaBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
