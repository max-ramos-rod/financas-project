from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.session import Base

class UserRole(str, enum.Enum):
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nome = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    contas = relationship("Conta", back_populates="user")
    categorias = relationship("Categoria", back_populates="user")
    transacoes = relationship("Transacao", back_populates="user")
    metas = relationship("Meta", back_populates="user")
    config_cristao = relationship("ConfiguracaoCristao", back_populates="user", uselist=False)
    delegacoes_enviadas = relationship(
        "Delegacao",
        foreign_keys="Delegacao.owner_user_id",
        back_populates="owner",
    )
    delegacoes_recebidas = relationship(
        "Delegacao",
        foreign_keys="Delegacao.delegate_user_id",
        back_populates="delegate",
    )
