"""Base contract for execution integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseIntegration(ABC):
    """Abstract integration adapter for executable actions."""

    name: str

    @abstractmethod
    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute the given action with the provided payload."""


# Backward-compatible alias for the earlier scaffold.
IntegrationBase = BaseIntegration
