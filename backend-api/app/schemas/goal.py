"""Goal schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.plan import PlanRead


class GoalCreateRequest(BaseModel):
    """Create a new goal inside a workspace."""

    workspace_id: UUID = Field(..., description="Workspace identifier")
    title: str = Field(..., min_length=1, max_length=255, description="Short goal title")
    goal_text: str = Field(..., min_length=5, description="Raw goal description")
    constraints: list[str] = Field(default_factory=list, description="Optional constraints")
    domain_hint: str | None = Field(default=None, max_length=128, description="Optional domain hint")
    trigger_planning: bool = Field(default=False, description="Whether to immediately call ai-service planning")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "workspace_id": "550e8400-e29b-41d4-a716-446655440001",
                    "title": "Prepare for backend interview",
                    "goal_text": "Help me prepare for a backend developer interview in 30 days.",
                    "constraints": ["30 days", "focus on Python and SQL"],
                    "domain_hint": "jobs",
                    "trigger_planning": True,
                }
            ]
        }
    )


class GoalRead(BaseModel):
    """Stored goal representation."""

    id: UUID = Field(..., description="Goal identifier")
    workspace_id: UUID = Field(..., description="Workspace identifier")
    title: str = Field(..., description="Human-readable goal title")
    goal_text: str = Field(..., description="Original goal text submitted by the user")
    constraints: list[str] = Field(default_factory=list, description="Constraints attached to the goal")
    domain_hint: str | None = Field(default=None, description="Optional domain hint")
    status: str = Field(..., description="Stored goal lifecycle status")
    interpreted_goal: dict[str, Any] | None = Field(default=None, description="ai-service interpreted goal payload")
    ai_response: dict[str, Any] | None = Field(default=None, description="Raw response returned from ai-service")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class GoalCreateResponse(BaseModel):
    """Goal creation response with optional plan preview."""

    goal: GoalRead = Field(..., description="Stored goal record")
    plan: PlanRead | None = Field(default=None, description="Optional plan returned when trigger_planning is true")
    planning_job_id: UUID | None = Field(default=None, description="Queued planning job identifier when planning is triggered")
