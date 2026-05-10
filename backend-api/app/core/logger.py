"""Logging helpers for the backend API."""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings


def setup_logger() -> None:
    """Configure application-wide logging once."""
    settings = get_settings()
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(settings.log_level.upper())
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    )

    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
