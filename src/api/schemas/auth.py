from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    email: EmailStr
    password_hash: str
    created_at: datetime
    updated_at: datetime | None = None
    tenant_id: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    updated_at: datetime | None = None
