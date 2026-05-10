"""Authentication business logic."""

from __future__ import annotations

from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead


class AuthService:
    """Encapsulates auth use cases away from API routes."""

    def register(self, db: Session, payload: RegisterRequest) -> TokenResponse:
        existing_user = db.scalar(select(User).where(User.email == payload.email))
        if existing_user is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return self._build_token_response(user)

    def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
        user = db.scalar(select(User).where(User.email == payload.email))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled")

        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        settings = get_settings()
        expires = timedelta(minutes=settings.access_token_expire_minutes)
        token = create_access_token(subject=str(user.id), expires_delta=expires)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=int(expires.total_seconds()),
            user=UserRead.model_validate(user),
        )
