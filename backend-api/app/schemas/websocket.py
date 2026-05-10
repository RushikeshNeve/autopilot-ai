"""WebSocket event schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


WebSocketEventType = Literal[
    "planning_started",
    "planning_progress",
    "planning_completed",
    "execution_job_submitted",
    "execution_job_running",
    "execution_job_completed",
    "execution_job_failed",
    "rag_ingestion_started",
    "rag_ingestion_completed",
]


class WebSocketEvent(BaseModel):
    """Structured realtime event sent to connected clients."""

    event_type: WebSocketEventType = Field(..., description="High-level event type")
    entity_type: str = Field(..., description="Entity category such as goal, plan, execution_job, or rag_document")
    entity_id: str = Field(..., description="Primary entity identifier")
    message: str = Field(..., description="Human-readable status message")
    data: dict[str, Any] = Field(default_factory=dict, description="Additional structured payload")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event creation timestamp in UTC",
    )

    model_config = ConfigDict(
        title="WebSocketEvent",
        json_schema_extra={
            "examples": [
                {
                    "event_type": "planning_started",
                    "entity_type": "goal",
                    "entity_id": "550e8400-e29b-41d4-a716-446655440002",
                    "message": "Planning has started for your goal.",
                    "data": {"goal_id": "550e8400-e29b-41d4-a716-446655440002"},
                    "timestamp": "2026-04-21T00:00:00Z",
                }
            ]
        }
    )
