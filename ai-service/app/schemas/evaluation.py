"""Evaluation schemas."""

from typing import List
from pydantic import BaseModel, Field


class CritiqueIssue(BaseModel):
    issue_type: str = Field(..., description="e.g. missing_dependency, vague_task")
    severity: str = Field(..., description="low, medium, high")
    description: str
    recommendation: str


class PlanCritique(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=1.0)
    issues: List[CritiqueIssue]
    strengths: List[str]
    summary: str


class CritiqueRequest(BaseModel):
    user_id: str
    plan: dict  # use FinalizedPlan in real system


class CritiqueResponse(BaseModel):
    critique: PlanCritique