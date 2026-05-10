"""Connection manager for realtime user-specific websocket channels."""

from __future__ import annotations

import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from app.core.logger import get_logger
from app.schemas.websocket import WebSocketEvent

logger = get_logger(__name__)


class ConnectionManager:
    """Track active websocket connections keyed by authenticated user ID."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """Accept and register a websocket for a user."""
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(websocket)
        logger.info("websocket_connected user_id=%s active_connections=%s", user_id, self.active_count(user_id))

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """Remove a websocket from the active registry."""
        async with self._lock:
            connections = self._connections.get(user_id)
            if connections is None:
                return
            connections.discard(websocket)
            if not connections:
                self._connections.pop(user_id, None)
        logger.info("websocket_disconnected user_id=%s active_connections=%s", user_id, self.active_count(user_id))

    async def send_to_user(self, user_id: str, event: WebSocketEvent) -> None:
        """Send an event to every active websocket for a user."""
        sockets = await self._snapshot_connections(user_id)
        for websocket in sockets:
            try:
                await websocket.send_json(event.model_dump(mode="json"))
            except WebSocketDisconnect:
                await self.disconnect(user_id, websocket)
            except Exception:
                logger.exception("websocket_send_failed user_id=%s entity_id=%s", user_id, event.entity_id)
                await self.disconnect(user_id, websocket)

    async def broadcast(self, event: WebSocketEvent) -> None:
        """Send an event to every active websocket across all users."""
        snapshots = await self._snapshot_all_connections()
        for user_id, sockets in snapshots.items():
            for websocket in sockets:
                try:
                    await websocket.send_json(event.model_dump(mode="json"))
                except WebSocketDisconnect:
                    await self.disconnect(user_id, websocket)
                except Exception:
                    logger.exception("websocket_broadcast_failed user_id=%s entity_id=%s", user_id, event.entity_id)
                    await self.disconnect(user_id, websocket)

    def active_count(self, user_id: str | None = None) -> int:
        """Return the number of active connections for a user or globally."""
        if user_id is None:
            return sum(len(connections) for connections in self._connections.values())
        return len(self._connections.get(user_id, set()))

    async def _snapshot_connections(self, user_id: str) -> list[WebSocket]:
        async with self._lock:
            return list(self._connections.get(user_id, set()))

    async def _snapshot_all_connections(self) -> dict[str, list[WebSocket]]:
        async with self._lock:
            return {user_id: list(connections) for user_id, connections in self._connections.items()}
