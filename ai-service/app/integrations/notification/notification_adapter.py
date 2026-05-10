"""Local notification adapter for execution jobs."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import uuid4

from app.services.execution.integration_base import BaseIntegration


class NotificationAdapter(BaseIntegration):
    """Record notification payloads in a durable local outbox."""

    name = "notification_adapter"
    action = "send_notification"

    _lock = RLock()
    _store_path = Path(__file__).resolve().parents[3] / ".data" / "notifications.json"

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != self.action:
            raise ValueError(f"Unsupported action for NotificationAdapter: {action}")

        task = payload.get("task") or {}
        decision = payload.get("decision") or {}
        record = {
            "notification_id": str(uuid4()),
            "integration": self.name,
            "action": action,
            "task_id": task.get("task_id"),
            "title": task.get("title") or "Notification",
            "message": self._build_message(task=task, decision=decision),
            "status": "recorded",
            "created_at": datetime.now(UTC).isoformat(),
            "local_only": True,
        }
        self._append_record(record)
        return record

    def _build_message(self, *, task: dict[str, Any], decision: dict[str, Any]) -> str:
        reason = str(decision.get("reason") or "Outbound communication requires review.")
        title = str(task.get("title") or "Untitled task")
        return f"{title}: {reason}"

    def _append_record(self, record: dict[str, Any]) -> None:
        with self._lock:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            records: list[dict[str, Any]] = []
            if self._store_path.exists():
                try:
                    loaded = json.loads(self._store_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, list):
                        records = [item for item in loaded if isinstance(item, dict)]
                except Exception:
                    records = []
            records.append(record)
            tmp_path = self._store_path.with_suffix(self._store_path.suffix + ".tmp")
            tmp_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
            tmp_path.replace(self._store_path)
