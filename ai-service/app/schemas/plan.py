from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.goal import GoalInterpretRequest, InterpretedGoal
from app.schemas.task import Milestone, TaskItem
from app.schemas.execution import ExecutionResponse
from app.schemas.evaluation import PlanCritique


class MilestonePlanResponse(BaseModel):
    user_id: str
    interpreted_goal: InterpretedGoal
    milestones: List[Milestone]


class InterpretedMilestonePlanRequest(BaseModel):
    user_id: str
    interpreted_goal: InterpretedGoal


class TaskPlanRequest(BaseModel):
    user_id: str
    interpreted_goal: InterpretedGoal
    milestone: Milestone


class TaskPlanResponse(BaseModel):
    user_id: str
    milestone: Milestone
    tasks: List[TaskItem]


class FinalizedPlan(BaseModel):
    user_id: str
    interpreted_goal: InterpretedGoal
    milestones: List[Milestone]
    tasks: List[TaskItem]
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    next_best_action: str = Field(...)


class FinalizePlanRequest(BaseModel):
    goal_request: GoalInterpretRequest
    interpreted_goal: Optional[InterpretedGoal] = None
    enable_revision: bool = True


class FinalizePlanResponse(BaseModel):
    plan: FinalizedPlan
    execution: Optional[ExecutionResponse] = None
    critique: Optional[PlanCritique] = None


class PlanRevisionRequest(BaseModel):
    user_id: str
    plan: FinalizedPlan
    critique: PlanCritique


class PlanRevisionResponse(BaseModel):
    plan: FinalizedPlan
