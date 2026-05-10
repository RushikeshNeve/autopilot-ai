"""Application configuration for the backend API."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    app_name: str = "backend-api"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = Field(default="postgresql+psycopg://postgres:postgres@localhost:5432/backend_api", validation_alias="DATABASE_URL")

    jwt_secret_key: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    ai_service_url: str = Field(default="http://127.0.0.1:8001", validation_alias="AI_SERVICE_URL")
    http_timeout_seconds: float = Field(default=120.0, validation_alias="HTTP_TIMEOUT_SECONDS")
    ai_finalize_timeout_seconds: float = Field(default=300.0, validation_alias="AI_FINALIZE_TIMEOUT_SECONDS")
    cors_origins: str = Field(
        default="http://127.0.0.1:3000,http://127.0.0.1:3001,http://localhost:3000,http://localhost:3001",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
