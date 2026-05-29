from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ConfiguracaoCristao(Base):
    __tablename__ = "config_cristao"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    modo_ativo = Column(Boolean, default=True)
    percentual_dizimo_padrao = Column(Float, default=10.0)
    categoria_dizimo_id = Column(Integer, ForeignKey("categorias.id"))
    igreja_nome = Column(String(200))
    igreja_endereco = Column(String(300))
    pastor_nome = Column(String(100))
    categoria_oferta_id = Column(Integer, ForeignKey("categorias.id"))
    categoria_missoes_id = Column(Integer, ForeignKey("categorias.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user = relationship("User", back_populates="config_cristao")
