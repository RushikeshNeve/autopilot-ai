"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserCreate, UserRead


class LoginRequest(BaseModel):
    """Login request payload."""

    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="User email address")
    password: str = Field(..., description="Plain text password")


class RegisterRequest(UserCreate):
    """Registration request payload."""


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: UserRead = Field(..., description="Authenticated user")

    model_config = ConfigDict(from_attributes=True)
