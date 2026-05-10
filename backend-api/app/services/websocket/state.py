"""Shared websocket singletons."""

from __future__ import annotations

from app.services.websocket.connection_manager import ConnectionManager
from app.services.websocket.event_publisher import EventPublisher


connection_manager = ConnectionManager()
event_publisher = EventPublisher(connection_manager)

