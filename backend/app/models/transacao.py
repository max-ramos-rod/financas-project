from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import StatusLiquidacao, TipoTransacao


class Transacao(Base):
    __tablename__ = "transacoes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    descricao = Column(String(200), nullable=False)
    valor = Column(Float, nullable=False)
    tipo = Column(Enum(TipoTransacao), nullable=False)
    data = Column(Date, nullable=False)
    data_vencimento = Column(Date, nullable=True)
    data_liquidacao = Column(Date, nullable=True)
    status_liquidacao = Column(Enum(StatusLiquidacao), nullable=False, default=StatusLiquidacao.PREVISTO)
    fixa = Column(Boolean, default=False)
    recorrente = Column(Boolean, default=False)
    confirmada = Column(Boolean, default=True)
    transacao_uuid = Column(String(36), unique=True, index=True, nullable=False)
    # Dízimo automático
    tem_dizimo = Column(Boolean, default=False)
    percentual_dizimo = Column(Float, default=10.0)
    transacao_dizimo_uuid = Column(String(36), index=True, nullable=True)
    e_dizimo = Column(Boolean, default=False)
    entrada_origem_id = Column(Integer, nullable=True)
    # Parcelamento
    parcelado = Column(Boolean, default=False)
    parcela_atual = Column(Integer)
    total_parcelas = Column(Integer)
    grupo_parcelamento_uuid = Column(String(36), index=True)
    # Empréstimo
    e_emprestimo = Column(Boolean, default=False)
    pessoa_emprestimo = Column(String(100))
    # Extras
    observacoes = Column(Text)
    tags = Column(String(500))
    valor_multa = Column(Float, nullable=False, default=0.0)
    valor_juros = Column(Float, nullable=False, default=0.0)
    valor_desconto = Column(Float, nullable=False, default=0.0)
    meta_id = Column(Integer, ForeignKey("metas.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship("User", back_populates="transacoes")
    conta = relationship("Conta", back_populates="transacoes")
    categoria = relationship("Categoria", back_populates="transacoes")
    meta = relationship("Meta", back_populates="transacoes")
