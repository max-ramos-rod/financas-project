from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db.session import Base

class TipoTransacao(str, enum.Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    TRANSFERENCIA = "transferencia"

class TipoConta(str, enum.Enum):
    CARTEIRA = "carteira"
    CONTA_CORRENTE = "conta_corrente"
    POUPANCA = "poupanca"
    CARTAO_CREDITO = "cartao_credito"
    INVESTIMENTO = "investimento"
    OUTRO = "outro"


class StatusLiquidacao(str, enum.Enum):
    PREVISTO = "previsto"
    LIQUIDADO = "liquidado"
    ATRASADO = "atrasado"
    CANCELADO = "cancelado"

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

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Pode ser nulo para categorias padrão do sistema
    nome = Column(String(100), nullable=False)
    icone = Column(String(50))
    cor = Column(String(7), default="#6B7280")
    tipo = Column(Enum(TipoTransacao), nullable=False) # Indica se é categoria de entrada, saída ou transferência
    padrao = Column(Boolean, default=False) # Indica se é uma categoria padrão do sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="categorias")
    transacoes = relationship("Transacao", back_populates="categoria")

class Transacao(Base):
    """SISTEMA DE DÍZIMO AUTOMÁTICO via UUID"""
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
    
    # UUID único de cada transação
    transacao_uuid = Column(String(36), unique=True, index=True, nullable=False)  # UUID único desta transação
    
    # DÍZIMO AUTOMÁTICO
    tem_dizimo = Column(Boolean, default=False)  # se TRUE, gera saída automática
    percentual_dizimo = Column(Float, default=10.0)  # % do dízimo (padrão 10%)
    transacao_dizimo_uuid = Column(String(36), index=True, nullable=True)  # UUID para relacionar entrada ↔ dízimo (compartilhado)
    e_dizimo = Column(Boolean, default=False)  # TRUE se esta transação É o dízimo gerado automaticamente
    entrada_origem_id = Column(Integer, nullable=True)  # ID da entrada que gerou este dízimo (se e_dizimo=True)
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


class DelegacaoStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REVOKED = "revoked"


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
