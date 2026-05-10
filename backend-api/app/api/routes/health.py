"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Service health response."""

    status: str = Field(..., description="Health status, typically ok")
    service: str = Field(..., description="Service name")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"status": "ok", "service": "backend-api"}]}
    )


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Return service health status for uptime and orchestration monitoring.",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    """Basic liveness endpoint."""
    return HealthResponse(status="ok", service="backend-api")
