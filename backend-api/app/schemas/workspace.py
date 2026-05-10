"""Workspace schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreateRequest(BaseModel):
    """Create a workspace for a user."""

    user_id: UUID = Field(..., description="Owner user ID")
    name: str = Field(..., min_length=1, max_length=255, description="Workspace name")
    description: str | None = Field(default=None, max_length=2000, description="Optional workspace description")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Career Growth",
                    "description": "Workspace for interview prep and job applications.",
                }
            ]
        }
    )


class WorkspaceRead(BaseModel):
    """Stored workspace representation."""

    id: UUID = Field(..., description="Workspace identifier")
    user_id: UUID = Field(..., description="Owner user identifier")
    name: str = Field(..., description="Workspace name")
    description: str | None = Field(default=None, description="Optional workspace description")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)
