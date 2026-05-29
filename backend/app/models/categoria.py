from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import TipoTransacao


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nome = Column(String(100), nullable=False)
    icone = Column(String(50))
    cor = Column(String(7), default="#6B7280")
    tipo = Column(Enum(TipoTransacao), nullable=False)
    padrao = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="categorias")
    transacoes = relationship("Transacao", back_populates="categoria")
