"""Database session setup."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.logger import get_logger

_session_factory: sessionmaker[Session] | None = None
logger = get_logger(__name__)

_sqlite_fallback_url = f"sqlite:///{(Path(tempfile.gettempdir()) / 'backend_api.db').as_posix()}"


def get_engine():
    """Create a SQLAlchemy engine lazily.

    The database driver is resolved only when the app actually needs a
    connection, which keeps imports lightweight and makes local bootstrapping
    failures easier to diagnose.
    """
    settings = get_settings()
    try:
        if settings.database_url.startswith("sqlite"):
            return create_engine(
                settings.database_url,
                connect_args={"check_same_thread": False},
                future=True,
            )
        return create_engine(
            settings.database_url,
            pool_pre_ping=True,
            future=True,
        )
    except (ModuleNotFoundError, OperationalError) as exc:
        if settings.app_env.lower() == "production":
            raise
        logger.warning(
            "database_fallback_to_sqlite reason=%s fallback_url=%s",
            exc,
            _sqlite_fallback_url,
        )
        return create_engine(
            _sqlite_fallback_url,
            connect_args={"check_same_thread": False},
            future=True,
        )


def get_session_factory() -> sessionmaker[Session]:
    """Return a cached SQLAlchemy session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
            class_=Session,
        )
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
