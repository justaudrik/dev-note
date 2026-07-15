from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ── Auth ──────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}


# ── Documents ─────────────────────────────────────────
class DocumentCreate(BaseModel):
    title: str = "Untitled Document"
    content: str = ""
    format: str = "plaintext"   # "markdown" or "plaintext"


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
