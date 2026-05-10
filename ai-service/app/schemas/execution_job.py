"""Execution job schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.execution import ExecutionDecision
from app.schemas.task import TaskItem


class ExecutionJobStatus(str, Enum):
    """Lifecycle states for an execution job."""

    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    requires_approval = "requires_approval"


class ExecutionJob(BaseModel):
    """Represents a single execution request and its lifecycle state."""

    model_config = ConfigDict(use_enum_values=True)

    job_id: str = Field(..., description="Unique execution job identifier")
    user_id: str = Field(..., description="User that owns the job")
    task: TaskItem = Field(..., description="Task to be executed")
    decision: ExecutionDecision = Field(..., description="Execution decision for the task")
    status: ExecutionJobStatus = Field(
        default=ExecutionJobStatus.queued,
        description="queued, running, completed, failed, requires_approval",
    )
    result: dict[str, Any] | None = Field(default=None, description="Execution result payload")
    error: str | None = Field(default=None, description="Error message if execution failed")

