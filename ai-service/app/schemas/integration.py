"""Integration status schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IntegrationStatus(BaseModel):
    """Describe a known integration and whether it is ready."""

    name: str
    capability: str
    tool_name: str
    status: Literal["available", "configured", "local_fallback", "missing_config", "unavailable"]
    description: str
    configured: bool = Field(default=False)
    requires_approval: bool = Field(default=False)
    notes: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)
