import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token, get_session_expire_delta, get_session_timeout_seconds
from app.crud import crud_password_reset
from app.crud.crud_user import (
    authenticate_user,
    create_google_user,
    create_user,
    get_user_by_email,
    get_user_by_google_id,
    link_google_account,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleLoginRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    Token,
    UserCreate,
    UserResponse,
)
from app.services.email import send_password_reset_email

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
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
@limiter.limit("20/minute")
def login(
    request: Request,
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
@limiter.limit("20/minute")
def login_google(
    request: Request,
    body: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Login com Google não está configurado neste servidor.",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        idinfo = id_token.verify_oauth2_token(
            body.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10,
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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("3/minute")
def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, body.email)
    if user:
        token_obj = crud_password_reset.criar_token(db, user.id)
        reset_url = f"{settings.FRONTEND_URL}/redefinir-senha?token={token_obj.token}"
        try:
            send_password_reset_email(to_email=body.email, reset_url=reset_url)
        except RuntimeError:
            # SMTP não configurado — mantém token acessível via log em dev
            logger.info(f"[DEV] Password reset token for {body.email}: {token_obj.token}")
    # Sempre retorna 200 — não revela se e-mail existe
    return ForgotPasswordResponse(message="Se o e-mail existir em nossa base, você receberá as instruções em breve.")


@router.post("/reset-password", response_model=ResetPasswordResponse)
@limiter.limit("5/minute")
def reset_password(request: Request, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_obj = crud_password_reset.buscar_token_valido(db, body.token)
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado.",
        )
    user = db.query(User).filter(User.id == token_obj.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(body.password)
    crud_password_reset.marcar_usado(db, token_obj)
    db.commit()
    return ResetPasswordResponse(message="Senha alterada com sucesso. Faça login com a nova senha.")
