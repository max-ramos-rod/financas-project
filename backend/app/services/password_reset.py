import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.password_reset_token import PasswordResetToken

TOKEN_TTL_HOURS = 1


class PasswordResetService:
    def criar_token(self, db: Session, user_id: int) -> PasswordResetToken:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        ).delete()

        token_str = secrets.token_urlsafe(48)
        expires = datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS)
        token_obj = PasswordResetToken(user_id=user_id, token=token_str, expires_at=expires)
        db.add(token_obj)
        db.commit()
        db.refresh(token_obj)
        return token_obj

    def buscar_token_valido(self, db: Session, token: str) -> Optional[PasswordResetToken]:
        now = datetime.now(timezone.utc)
        return db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > now,
            PasswordResetToken.used_at.is_(None),
        ).first()

    def marcar_usado(self, db: Session, token_obj: PasswordResetToken) -> None:
        token_obj.used_at = datetime.now(timezone.utc)
        db.commit()
