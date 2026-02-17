from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import date, datetime
from app.models import TipoTransacao, StatusLiquidacao

class TransacaoBase(BaseModel):
    conta_id: int
    categoria_id: Optional[int] = None
    descricao: str = Field(..., min_length=1, max_length=200)
    valor: float = Field(..., gt=0)
    tipo: TipoTransacao
    data: date
    data_vencimento: Optional[date] = None
    data_liquidacao: Optional[date] = None
    status_liquidacao: StatusLiquidacao = StatusLiquidacao.PREVISTO
    fixa: bool = False
    recorrente: bool = False
    confirmada: bool = True
    
    # Dízimo
    tem_dizimo: bool = False
    percentual_dizimo: float = Field(default=10.0, ge=0, le=100)
    
    # Parcelamento
    parcelado: bool = False
    total_parcelas: Optional[int] = Field(None, ge=2, le=48)
    
    # Empréstimo
    e_emprestimo: bool = False
    pessoa_emprestimo: Optional[str] = Field(None, max_length=100)
    
    # Extras
    observacoes: Optional[str] = None
    tags: Optional[str] = None
    valor_multa: float = Field(default=0, ge=0)
    valor_juros: float = Field(default=0, ge=0)
    valor_desconto: float = Field(default=0, ge=0)
    meta_id: Optional[int] = None

    @model_validator(mode="after")
    def validar_parcelamento(self):
        if self.total_parcelas and self.total_parcelas > 1:
            self.parcelado = True
        if self.parcelado and (not self.total_parcelas or self.total_parcelas < 2):
            raise ValueError("Para parcelamento, informe total_parcelas >= 2.")
        if not self.parcelado:
            self.total_parcelas = None
        return self

class TransacaoCreate(TransacaoBase):
    """Schema para criação de transação"""
    pass

class TransacaoUpdate(BaseModel):
    """Schema para atualização de transação"""
    conta_id: Optional[int] = None
    categoria_id: Optional[int] = None
    descricao: Optional[str] = Field(None, min_length=1, max_length=200)
    valor: Optional[float] = Field(None, gt=0)
    tipo: Optional[TipoTransacao] = None
    data: Optional[date] = None
    data_vencimento: Optional[date] = None
    data_liquidacao: Optional[date] = None
    status_liquidacao: Optional[StatusLiquidacao] = None
    fixa: Optional[bool] = None
    recorrente: Optional[bool] = None
    confirmada: Optional[bool] = None
    tem_dizimo: Optional[bool] = None
    percentual_dizimo: Optional[float] = Field(default=None, ge=0, le=100)
    observacoes: Optional[str] = None
    tags: Optional[str] = None
    valor_multa: Optional[float] = Field(default=None, ge=0)
    valor_juros: Optional[float] = Field(default=None, ge=0)
    valor_desconto: Optional[float] = Field(default=None, ge=0)
    meta_id: Optional[int] = None

class TransacaoResponse(TransacaoBase):
    """Schema de resposta com dados completos"""
    id: int
    user_id: int
    
    # UUID único desta transação
    transacao_uuid: str
    
    # Campos de dízimo
    transacao_dizimo_uuid: Optional[str] = None
    e_dizimo: bool = False
    entrada_origem_id: Optional[int] = None
    
    # Parcelamento
    parcela_atual: Optional[int] = None
    grupo_parcelamento_uuid: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
