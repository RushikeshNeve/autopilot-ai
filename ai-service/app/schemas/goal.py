"""Goal schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class GoalInterpretRequest(BaseModel):
    user_id: str = Field(..., description="Unique user ID")
    goal_text: str = Field(..., min_length=5, description="Raw natural language goal")
    constraints: List[str] = Field(default_factory=list)
    domain_hint: Optional[str] = Field(default=None, description="Optional domain hint")


class InterpretedGoal(BaseModel):
    primary_intent: str = Field(..., description="Main intent of the goal")
    sub_intents: List[str] = Field(default_factory=list)
    domain: str = Field(..., description="Detected domain such as career, study, fitness")
    target_outcomes: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    estimated_horizon: str = Field(..., description="E.g. 2_weeks, 3_months")
    urgency: str = Field(..., description="low, medium, high")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning_summary: str = Field(..., description="Short safe explanation of interpretation")


class GoalInterpretResponse(BaseModel):
    user_id: str
    interpreted_goal: InterpretedGoal