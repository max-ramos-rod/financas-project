from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Busca usuário por ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca usuário por email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_google_id(db: Session, google_id: str) -> Optional[User]:
    """Busca usuário pelo google_id"""
    return db.query(User).filter(User.google_id == google_id).first()


def create_google_user(db: Session, email: str, nome: str, google_id: str, avatar_url: Optional[str] = None) -> User:
    """Cria usuário autenticado via Google (sem senha local)"""
    db_user = User(
        email=email,
        nome=nome,
        hashed_password=None,
        google_id=google_id,
        avatar_url=avatar_url,
        role="user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def link_google_account(db: Session, user: User, google_id: str, avatar_url: Optional[str] = None) -> User:
    """Vincula Google a uma conta local existente"""
    user.google_id = google_id
    if avatar_url:
        user.avatar_url = avatar_url
    db.commit()
    db.refresh(user)
    return user


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
