"""Singleton websocket dependencies."""

from __future__ import annotations

from app.services.websocket.connection_manager import ConnectionManager
from app.services.websocket.event_publisher import EventPublisher
from app.services.websocket.state import connection_manager, event_publisher


def get_connection_manager() -> ConnectionManager:
    """Return the shared websocket connection manager."""
    return connection_manager


def get_event_publisher() -> EventPublisher:
    """Return the shared websocket event publisher."""
    return event_publisher
