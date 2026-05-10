"""WebSocket gateway for authenticated realtime progress updates."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_access_token
from app.core.logger import get_logger
from app.services.websocket.state import connection_manager

router = APIRouter(tags=["websocket"])
logger = get_logger(__name__)


@router.websocket("/ws")
async def websocket_gateway(websocket: WebSocket) -> None:
    """Authenticate a websocket connection and keep it open for realtime events."""
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_access_token(token)
        user_id = str(payload.get("sub") or "")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(user_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            logger.info("websocket_message_received user_id=%s message=%s", user_id, message)
    except WebSocketDisconnect:
        await connection_manager.disconnect(user_id, websocket)
    except Exception:
        logger.exception("websocket_gateway_error user_id=%s", user_id)
        await connection_manager.disconnect(user_id, websocket)
