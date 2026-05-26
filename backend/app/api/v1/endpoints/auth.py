from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token, get_session_expire_delta, get_session_timeout_seconds
from app.crud.crud_user import (
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_google_id,
    create_google_user,
    link_google_account,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse, GoogleLoginRequest

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = create_user(
        db=db,
        email=user_in.email,
        password=user_in.password,
        nome=user_in.nome,
        role=user_in.role,
    )

    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.email)},
        expires_delta=get_session_expire_delta(),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": get_session_timeout_seconds(),
    }


@router.post("/refresh-session", response_model=Token)
def refresh_session(current_user: User = Depends(get_current_active_user)):
    access_token = create_access_token(
        data={"sub": str(current_user.email)},
        expires_delta=get_session_expire_delta(),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": get_session_timeout_seconds(),
    }


@router.post("/google", response_model=Token)
def login_google(
    body: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Login com Google não está configurado neste servidor.",
        )

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token Google inválido ou expirado.",
        )

    google_id: str = idinfo["sub"]
    email: str = idinfo.get("email", "")
    nome: str = idinfo.get("name") or email.split("@")[0]
    avatar_url: str | None = idinfo.get("picture")

    user = get_user_by_google_id(db, google_id)

    if not user:
        existing = get_user_by_email(db, email)
        if existing:
            user = link_google_account(db, existing, google_id, avatar_url)
        else:
            user = create_google_user(db, email=email, nome=nome, google_id=google_id, avatar_url=avatar_url)

    access_token = create_access_token(
        data={"sub": str(user.email)},
        expires_delta=get_session_expire_delta(),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": get_session_timeout_seconds(),
    }


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
