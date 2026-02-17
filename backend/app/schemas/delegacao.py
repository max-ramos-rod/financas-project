from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class DelegacaoInviteRequest(BaseModel):
    email: EmailStr
    can_write: bool = True


class DelegacaoConfirmRequest(BaseModel):
    nome: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserResumo(BaseModel):
    id: int
    nome: str
    email: EmailStr

    class Config:
        from_attributes = True


class DelegacaoResponse(BaseModel):
    id: int
    owner_user_id: int
    delegate_user_id: Optional[int]
    invited_email: EmailStr
    status: str
    can_write: bool
    invite_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    owner: UserResumo
    delegate: Optional[UserResumo] = None

    class Config:
        from_attributes = True


class DelegacaoInviteResponse(BaseModel):
    delegacao: DelegacaoResponse
    has_account: bool
    email_sent: bool


class DelegacaoContextOption(BaseModel):
    user_id: int
    nome: str
    email: EmailStr
    can_write: bool
    is_owner: bool


class DelegacaoInviteTokenInfo(BaseModel):
    invited_email: EmailStr
    owner_nome: str
    owner_email: EmailStr
    has_account: bool
    expired: bool
