"""Goal business logic."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Goal, Workspace
from app.schemas.goal import GoalCreateRequest


class GoalService:
    """Goal CRUD and state update operations."""

    def create_goal(self, db: Session, payload: GoalCreateRequest) -> Goal:
        workspace = db.get(Workspace, payload.workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        goal = Goal(
            workspace_id=payload.workspace_id,
            title=payload.title,
            goal_text=payload.goal_text,
            constraints=payload.constraints,
            domain_hint=payload.domain_hint,
            status="created",
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    def get_goal(self, db: Session, goal_id: UUID) -> Goal:
        goal = db.get(Goal, goal_id)
        if goal is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        return goal

    def update_goal_ai_response(
        self,
        db: Session,
        goal_id: UUID,
        *,
        status_value: str,
        interpreted_goal: dict | None = None,
        ai_response: dict | None = None,
    ) -> Goal:
        goal = self.get_goal(db, goal_id)
        goal.status = status_value
        if interpreted_goal is not None:
            goal.interpreted_goal = interpreted_goal
        if ai_response is not None:
            goal.ai_response = ai_response
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal
