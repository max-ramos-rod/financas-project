#!/bin/bash
cd "$(dirname "$0")/backend"

# ===== MODELS =====

# user.py
cat > app/models/user.py << 'EOF'
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
EOF

# financeiro.py com SISTEMA DE DÍZIMO
cat > app/models/financeiro.py << 'EOF'
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum, Date
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
    INVESTIMENTO = "investimento"
    OUTRO = "outro"

class Conta(Base):
    __tablename__ = "contas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    tipo = Column(Enum(TipoConta), nullable=False)
    saldo = Column(Float, default=0.0)
    cor = Column(String(7), default="#3B82F6")
    ativa = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="contas")
    transacoes = relationship("Transacao", back_populates="conta")

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nome = Column(String(100), nullable=False)
    icone = Column(String(50))
    cor = Column(String(7), default="#6B7280")
    tipo = Column(Enum(TipoTransacao))
    padrao = Column(Boolean, default=False)
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
    fixa = Column(Boolean, default=False)
    recorrente = Column(Boolean, default=False)
    confirmada = Column(Boolean, default=True)
    # DÍZIMO AUTOMÁTICO
    tem_dizimo = Column(Boolean, default=False)
    percentual_dizimo = Column(Float, default=10.0)
    transacao_dizimo_uuid = Column(String(36), unique=True, index=True)
    e_dizimo = Column(Boolean, default=False)
    entrada_origem_id = Column(Integer)
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
EOF

# models/__init__.py
cat > app/models/__init__.py << 'EOF'
from .user import User, UserRole
from .financeiro import (
    Conta, TipoConta, Categoria, Transacao, TipoTransacao,
    Meta, Orcamento, ConfiguracaoCristao
)

__all__ = [
    "User", "UserRole", "Conta", "TipoConta", "Categoria",
    "Transacao", "TipoTransacao", "Meta", "Orcamento", "ConfiguracaoCristao"
]
EOF

# ===== DB =====

cat > app/db/session.py << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
EOF

cat > app/db/__init__.py << 'EOF'
from .session import Base, get_db, engine

__all__ = ["Base", "get_db", "engine"]
EOF

# ===== CORE =====

cat > app/core/config.py << 'EOF'
from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finanças Cristãs API"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    DATABASE_URL: str = "postgresql://financas_user:financas_pass@localhost:5432/financas_db"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
EOF

cat > app/core/security.py << 'EOF'
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
EOF

cat > app/core/__init__.py << 'EOF'
from .config import settings
from .security import verify_password, get_password_hash, create_access_token, decode_token

__all__ = ["settings", "verify_password", "get_password_hash", "create_access_token", "decode_token"]
EOF

# ===== MAIN =====

cat > app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Finanças Cristãs API", "status": "online"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
EOF

cat > app/__init__.py << 'EOF'
# App package
EOF

# ===== ALEMBIC =====

cat > alembic/env.py << 'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.db.session import Base
from app.models import *

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

cat > alembic/script.py.mako << 'EOF'
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
EOF

echo "✅ Arquivos backend criados!"
ls -R app/

