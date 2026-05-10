"""Task schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Milestone(BaseModel):
    milestone_id: str = Field(..., description="Unique milestone identifier")
    title: str = Field(..., description="Short milestone title")
    description: str = Field(..., description="What this milestone covers")
    priority: str = Field(..., description="low, medium, high")
    estimated_duration_days: Optional[int] = Field(default=None, ge=1)


class TaskItem(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    milestone_id: str = Field(..., description="Linked milestone identifier")
    title: str = Field(..., description="Short task title")
    description: str = Field(..., description="Detailed task description")
    task_type: str = Field(..., description="planning, study, execution, review, drafting")
    priority: str = Field(..., description="low, medium, high")
    estimated_minutes: Optional[int] = Field(default=None, ge=5)
    dependencies: List[str] = Field(default_factory=list)
    requires_approval: bool = Field(default=False)
    suggested_tools: List[str] = Field(default_factory=list)