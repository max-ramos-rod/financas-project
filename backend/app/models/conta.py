from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import TipoConta


class Conta(Base):
    __tablename__ = "contas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    tipo = Column(Enum(TipoConta), nullable=False)
    saldo = Column(Float, default=0.0)
    dia_fechamento = Column(Integer, nullable=True)
    dia_vencimento = Column(Integer, nullable=True)
    limite_credito = Column(Float, nullable=True)
    cor = Column(String(7), default="#3B82F6")
    ativa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="contas")
    transacoes = relationship("Transacao", back_populates="conta")
    ciclos_fatura = relationship("ContaCartaoCiclo", back_populates="conta", cascade="all, delete-orphan")


class ContaCartaoCiclo(Base):
    __tablename__ = "conta_cartao_ciclos"
    __table_args__ = (
        UniqueConstraint("conta_id", "competencia_ano", "competencia_mes", name="uq_conta_cartao_ciclo_competencia"),
    )

    id = Column(Integer, primary_key=True, index=True)
    conta_id = Column(Integer, ForeignKey("contas.id"), nullable=False)
    competencia_ano = Column(Integer, nullable=False)
    competencia_mes = Column(Integer, nullable=False)
    data_fechamento_prevista = Column(Date, nullable=False)
    data_fechamento_real = Column(Date, nullable=True)
    data_vencimento_prevista = Column(Date, nullable=False)
    data_vencimento_real = Column(Date, nullable=True)
    observacao = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    conta = relationship("Conta", back_populates="ciclos_fatura")
