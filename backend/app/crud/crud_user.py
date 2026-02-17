from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash, verify_password
from typing import Optional


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Busca usuário por ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email"""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, password: str, nome: str, role: str) -> User:
    """Cria novo usuário"""
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        nome=nome,
        hashed_password=hashed_password,
        role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Autentica usuário"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Atualiza usuário"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user
