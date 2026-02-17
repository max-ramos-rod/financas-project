from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models import DelegacaoStatus
from app.crud.crud_user import get_user_by_email
from app.crud.crud_delegacao import get_active_delegacao

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass
class AccessContext:
    actor_user: User
    effective_user: User
    delegated: bool
    can_write: bool


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Retorna o usuário atual baseado no token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise credentials_exception

    email = subject.strip()
    if not email:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Retorna o usuário ativo atual"""
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Verifica se o usuário é admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_access_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccessContext:
    """
    Resolve o contexto de acesso efetivo.

    - `actor_user`: usuário autenticado no token.
    - `effective_user`: dono dos dados a serem acessados.
    """
    act_as_raw = request.headers.get("X-Act-As-User")
    if not act_as_raw:
        return AccessContext(
            actor_user=current_user,
            effective_user=current_user,
            delegated=False,
            can_write=True,
        )

    try:
        owner_user_id = int(act_as_raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Act-As-User inválido",
        ) from exc

    if owner_user_id == current_user.id:
        return AccessContext(
            actor_user=current_user,
            effective_user=current_user,
            delegated=False,
            can_write=True,
        )

    delegacao = get_active_delegacao(
        db=db,
        owner_user_id=owner_user_id,
        delegate_user_id=current_user.id,
    )
    if not delegacao or delegacao.status != DelegacaoStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Delegação não encontrada ou inativa",
        )

    owner_user = db.query(User).filter(User.id == owner_user_id).first()
    if not owner_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário dono dos dados não encontrado",
        )

    if request.method.upper() in WRITE_METHODS and not delegacao.can_write:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Delegação sem permissão de escrita",
        )

    return AccessContext(
        actor_user=current_user,
        effective_user=owner_user,
        delegated=True,
        can_write=delegacao.can_write,
    )
