"""Deterministic scheduler adapter for execution jobs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.execution.integration_base import BaseIntegration


class SchedulerAdapter(BaseIntegration):
    """Create a structured schedule suggestion for a task."""

    name = "scheduler_adapter"
    action = "schedule_item"

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != self.action:
            raise ValueError(f"Unsupported action for SchedulerAdapter: {action}")

        task = payload.get("task") or {}
        decision = payload.get("decision") or {}
        estimated_minutes = task.get("estimated_minutes")
        priority = str(task.get("priority") or "medium").lower()

        base_delay_hours = 4 if priority == "high" else 24 if priority == "medium" else 48
        scheduled_for = datetime.now(UTC) + timedelta(hours=base_delay_hours)
        duration_minutes = int(estimated_minutes) if isinstance(estimated_minutes, int) else 30

        return {
            "integration": self.name,
            "action": action,
            "task_id": task.get("task_id"),
            "scheduled_for": scheduled_for.isoformat(),
            "duration_minutes": duration_minutes,
            "summary": f"Schedule {task.get('title') or 'task'} for focused execution.",
            "decision": decision,
            "local_only": True,
        }
