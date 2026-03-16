"""
ByggSjekk – Authentication & user schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Token schemas
# ---------------------------------------------------------------------------


class Token(BaseModel):
    """Response body for a successful login."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded JWT payload."""

    sub: str | None = None  # user id


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Body for POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=512)
    is_architect: bool = False


class UserLogin(BaseModel):
    """Body for form-based login (used internally; OAuth2 form is handled by FastAPI)."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Safe user representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_architect: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    """Partial update payload for the current user."""

    full_name: str | None = Field(default=None, max_length=512)
    password: str | None = Field(default=None, min_length=8, max_length=128)
