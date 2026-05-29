from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    nome: str
    role: UserRole


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GoogleLoginRequest(BaseModel):
    credential: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    email: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=6)


class ResetPasswordResponse(BaseModel):
    message: str
