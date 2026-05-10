"""Workspace business logic."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, Workspace
from app.schemas.workspace import WorkspaceCreateRequest


class WorkspaceService:
    """Workspace CRUD operations."""

    def create_workspace(self, db: Session, payload: WorkspaceCreateRequest) -> Workspace:
        owner = db.get(User, payload.user_id)
        if owner is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        workspace = Workspace(
            user_id=payload.user_id,
            name=payload.name,
            description=payload.description,
        )
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        return workspace

    def get_workspace(self, db: Session, workspace_id: UUID) -> Workspace:
        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        return workspace

    def list_workspaces_for_user(self, db: Session, user_id: UUID) -> list[Workspace]:
        return db.scalars(select(Workspace).where(Workspace.user_id == user_id).order_by(Workspace.created_at.desc())).all()
