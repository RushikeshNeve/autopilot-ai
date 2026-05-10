"""Execution schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.task import TaskItem


class ExecutionDecision(BaseModel):
    task_id: str
    action_mode: str = Field(
        ...,
        description="suggest, auto_execute, requires_approval, manual"
    )
    tool_category: Optional[str] = Field(
        default=None,
        description="retrieve_knowledge, generate_content, store_data, schedule, notify"
    )
    tool_name: Optional[str] = Field(
        default=None,
        description="Optional concrete integration/tool name"
    )
    domain: Optional[str] = Field(
        default=None,
        description="Optional domain like study, jobs, fitness"
    )
    reason: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExecutionRequest(BaseModel):
    user_id: str
    tasks: List[TaskItem]


class ExecutionResponse(BaseModel):
    user_id: str
    decisions: List[ExecutionDecision]