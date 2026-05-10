"""Plan schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExecutionDecision(BaseModel):
    """A task-level execution decision returned by ai-service."""

    task_id: str = Field(..., description="Identifier of the task being routed")
    action_mode: Literal["suggest", "auto_execute", "requires_approval", "manual"] = Field(
        ...,
        description="How backend-api should treat the task",
    )
    tool_category: str | None = Field(default=None, description="Capability category such as retrieve_knowledge or store_data")
    tool_name: str | None = Field(default=None, description="Concrete integration/tool name if available")
    domain: str | None = Field(default=None, description="Optional domain such as study, jobs, or fitness")
    reason: str = Field(..., description="Why this action mode was selected")
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExecutionJobSummary(BaseModel):
    """Short summary of an execution job created in ai-service."""

    job_id: str = Field(..., description="Execution job identifier returned by ai-service")
    status: str = Field(..., description="Current job status")
    task_id: str = Field(..., description="Task identifier associated with the job")
    action_mode: str = Field(..., description="Action mode used when creating the job")


class PlanFinalizeRequest(BaseModel):
    """Request to finalize a plan for a goal."""

    goal_id: UUID = Field(..., description="Goal identifier")
    submit_execution_jobs: bool = Field(
        default=False,
        description="Whether to submit execution jobs for auto-execute or approval-ready decisions",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "goal_id": "550e8400-e29b-41d4-a716-446655440002",
                    "submit_execution_jobs": True,
                }
            ]
        }
    )


class PlanFinalizeJobCreateResponse(BaseModel):
    """Response returned when a plan finalization job is queued."""

    job_id: str = Field(..., description="Plan finalization job identifier")
    status: Literal["queued"] = Field(default="queued", description="Initial job status")


class PlanFinalizeJobRead(BaseModel):
    """Frontend-friendly plan finalization job status."""

    job_id: str = Field(..., description="Plan finalization job identifier")
    goal_id: UUID = Field(..., description="Related goal identifier")
    workspace_id: UUID = Field(..., description="Related workspace identifier")
    user_id: UUID = Field(..., description="Owning user identifier")
    status: Literal["queued", "running", "completed", "failed"] = Field(..., description="Current job status")
    result: PlanFinalizeResponse | None = Field(default=None, description="Completed plan result")
    error: str | None = Field(default=None, description="Failure message if the job failed")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class PlanRead(BaseModel):
    """Frontend-friendly stored plan result."""

    id: UUID
    goal_id: UUID
    status: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any] | None = None
    execution_decisions: list[ExecutionDecision] = Field(default_factory=list)
    approval_ready_execution_decisions: list[ExecutionDecision] = Field(default_factory=list)
    execution_jobs: list[ExecutionJobSummary] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PlanFinalizeResponse(BaseModel):
    """Response returned after plan finalization."""

    plan: PlanRead
    raw_ai_response: dict[str, Any] = Field(..., description="Raw response returned by ai-service")
