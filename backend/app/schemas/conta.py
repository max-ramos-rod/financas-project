from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from app.models import TipoConta

class ContaBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    tipo: TipoConta
    dia_fechamento: Optional[int] = Field(default=None, ge=1, le=31)
    dia_vencimento: Optional[int] = Field(default=None, ge=1, le=31)
    limite_credito: Optional[float] = Field(default=None, ge=0)
    cor: str
    ativa: bool = True

class ContaCreate(ContaBase):
    saldo: float = Field(default=0.0, ge=-999999999, le=999999999)

    @model_validator(mode="after")
    def validar_cartao_credito(self):
        if self.tipo == TipoConta.CARTAO_CREDITO:
            if self.dia_fechamento is None or self.dia_vencimento is None:
                raise ValueError("Conta de cartao exige dia_fechamento e dia_vencimento.")
        else:
            self.dia_fechamento = None
            self.dia_vencimento = None
            self.limite_credito = None
        return self

class ContaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    tipo: Optional[TipoConta] = None
    saldo: Optional[float] = Field(None, ge=-999999999, le=999999999)
    dia_fechamento: Optional[int] = Field(default=None, ge=1, le=31)
    dia_vencimento: Optional[int] = Field(default=None, ge=1, le=31)
    limite_credito: Optional[float] = Field(default=None, ge=0)
    cor: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    ativa: Optional[bool] = None

class ContaResponse(ContaBase):
    id: int
    user_id: int
    saldo: float
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FaturaItemResponse(BaseModel):
    transacao_id: int
    descricao: str
    data: date
    data_vencimento: Optional[date] = None
    status_liquidacao: str
    valor: float
    valor_multa: float = 0
    valor_juros: float = 0
    valor_desconto: float = 0
    valor_efetivo: float


class FaturaResumoResponse(BaseModel):
    conta_id: int
    conta_nome: str
    periodo_inicio: date
    periodo_fim: date
    dia_fechamento: int
    dia_vencimento: int
    data_vencimento_fatura: date
    total_itens: int
    valor_total: float
    itens: List[FaturaItemResponse]


class PagarFaturaRequest(BaseModel):
    conta_pagamento_id: int
    data_pagamento: Optional[date] = None
    descricao: Optional[str] = None
