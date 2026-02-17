from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class OrcamentoBase(BaseModel):
    categoria_id: int
    mes: int = Field(..., ge=1, le=12)
    ano: int = Field(..., ge=2000, le=2100)
    valor_planejado: float = Field(..., gt=0)

class OrcamentoCreate(OrcamentoBase):
    pass

class OrcamentoUpdate(BaseModel):
    categoria_id: Optional[int] = None
    mes: Optional[int] = Field(None, ge=1, le=12)
    ano: Optional[int] = Field(None, ge=2000, le=2100)
    valor_planejado: Optional[float] = Field(None, gt=0)

class OrcamentoResponse(OrcamentoBase):
    id: int
    user_id: int
    valor_gasto: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True