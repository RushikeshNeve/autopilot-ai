"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "AI Service"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    log_level: str = "INFO"

    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", validation_alias="OPENAI_MODEL")
    openai_timeout: int = Field(default=120, validation_alias="OPENAI_TIMEOUT")
    openai_max_retries: int = Field(default=1, validation_alias="OPENAI_MAX_RETRIES")
    notion_api_key: str = Field(default="", validation_alias="NOTION_API_KEY")
    notion_db_id: str = Field(default="", validation_alias="NOTION_DB_ID")
    qdrant_host: str = Field(default="localhost", validation_alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, validation_alias="QDRANT_PORT")
    qdrant_collection_name: str = Field(default="rag_chunks", validation_alias="QDRANT_COLLECTION_NAME")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
