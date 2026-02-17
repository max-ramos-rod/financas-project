from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from app.models.financeiro import TipoTransacao

class CategoriaBase(BaseModel):
    user_id: Optional[int] = None
    nome: str = Field(..., min_length=1, max_length=100)
    icone: Optional[str] = Field(default=None, max_length=50)
    cor: str = Field(default="#6B7280", pattern="^#[0-9A-Fa-f]{6}$")
    tipo: TipoTransacao
    padrao: bool = False

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    icone: Optional[str] = Field(default=None, max_length=50)
    cor: Optional[str] = Field(default=None, pattern="^#[0-9A-Fa-f]{6}$")
    tipo: Optional[TipoTransacao] = None


class CategoriaResponse(CategoriaBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
