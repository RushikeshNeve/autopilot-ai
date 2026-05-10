"""Helpers for publishing structured websocket events."""

from __future__ import annotations

from typing import Any

from app.schemas.websocket import WebSocketEvent, WebSocketEventType
from app.services.websocket.connection_manager import ConnectionManager


class EventPublisher:
    """Create and publish structured realtime events."""

    def __init__(self, connection_manager: ConnectionManager) -> None:
        self._connection_manager = connection_manager

    async def publish_to_user(
        self,
        user_id: str,
        *,
        event_type: WebSocketEventType,
        entity_type: str,
        entity_id: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> WebSocketEvent:
        """Publish an event to a single user."""
        event = self._build_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            data=data,
        )
        await self._connection_manager.send_to_user(user_id, event)
        return event

    async def broadcast(
        self,
        *,
        event_type: WebSocketEventType,
        entity_type: str,
        entity_id: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> WebSocketEvent:
        """Broadcast an event to all connected users."""
        event = self._build_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            data=data,
        )
        await self._connection_manager.broadcast(event)
        return event

    def _build_event(
        self,
        *,
        event_type: WebSocketEventType,
        entity_type: str,
        entity_id: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> WebSocketEvent:
        """Construct a typed websocket event."""
        return WebSocketEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            data=data or {},
        )
