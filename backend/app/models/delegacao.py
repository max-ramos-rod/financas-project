from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base
from app.models.enums import DelegacaoStatus


class Delegacao(Base):
    __tablename__ = "delegacoes"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "delegate_user_id", name="uq_delegacoes_owner_delegate"),
    )

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delegate_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_email = Column(String(255), nullable=False, index=True)
    invite_token = Column(String(128), unique=True, index=True, nullable=True)
    invite_expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(DelegacaoStatus), nullable=False, default=DelegacaoStatus.PENDING)
    can_write = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    owner = relationship("User", foreign_keys=[owner_user_id], back_populates="delegacoes_enviadas")
    delegate = relationship("User", foreign_keys=[delegate_user_id], back_populates="delegacoes_recebidas")
