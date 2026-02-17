from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    nome: str
    role: UserRole


# Create schemas
class UserCreate(UserBase):
    password: str


# Update schemas
class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None


# Response schemas
class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None