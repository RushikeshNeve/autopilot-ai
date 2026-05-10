"""Workspace routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workspace import WorkspaceCreateRequest, WorkspaceRead
from app.services.workspaces.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

workspace_service = WorkspaceService()


@router.post(
    "",
    response_model=WorkspaceRead,
    summary="Create workspace",
    description="Create a new workspace for organizing goals, plans, and related AI outputs.",
)
def create_workspace(payload: WorkspaceCreateRequest, db: Session = Depends(get_db)) -> WorkspaceRead:
    try:
        return WorkspaceRead.model_validate(workspace_service.create_workspace(db, payload))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "/{workspace_id}",
    response_model=WorkspaceRead,
    summary="Get workspace",
    description="Fetch a workspace by its identifier.",
)
def get_workspace(workspace_id: UUID, db: Session = Depends(get_db)) -> WorkspaceRead:
    try:
        return WorkspaceRead.model_validate(workspace_service.get_workspace(db, workspace_id))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[WorkspaceRead],
    summary="List workspaces",
    description="List all workspaces for a specific user.",
)
def list_workspaces(user_id: UUID = Query(..., description="Owner user identifier"), db: Session = Depends(get_db)) -> list[WorkspaceRead]:
    try:
        workspaces = workspace_service.list_workspaces_for_user(db, user_id)
        return [WorkspaceRead.model_validate(workspace) for workspace in workspaces]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
