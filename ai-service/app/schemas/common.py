"""Common shared schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str = Field(..., examples=["ai-service"])


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["An error occurred."])