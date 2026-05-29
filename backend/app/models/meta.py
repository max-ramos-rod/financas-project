from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Meta(Base):
    __tablename__ = "metas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text)
    valor_alvo = Column(Float, nullable=False)
    valor_atual = Column(Float, default=0.0)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date)
    concluida = Column(Boolean, default=False)
    cor = Column(String(7), default="#10B981")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="metas")
    transacoes = relationship("Transacao", back_populates="meta")
