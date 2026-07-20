from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional


# ── Auth ──────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: EmailStr       # pydantic validates RFC 5321 format; requires email-validator package
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Username must be at least 2 characters")
        if len(v) > 30:
            raise ValueError("Username must be at most 30 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}


# ── Documents ─────────────────────────────────────────────────
class DocumentCreate(BaseModel):
    title: str = "Untitled Document"
    content: str = ""
    format: str = "plaintext"


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None
    is_pinned: Optional[bool] = None


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    format: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    