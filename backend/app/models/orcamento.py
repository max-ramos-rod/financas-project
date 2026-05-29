from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Orcamento(Base):
    __tablename__ = "orcamentos"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    mes = Column(Integer, nullable=False)
    ano = Column(Integer, nullable=False)
    valor_planejado = Column(Float, nullable=False)
    valor_gasto = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User")
    categoria = relationship("Categoria")
