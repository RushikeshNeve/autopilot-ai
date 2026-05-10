"""Notion integration adapter."""

from __future__ import annotations

from typing import Any

import requests

from app.core.config import get_settings
from app.services.execution.integration_base import BaseIntegration


class NotionAdapter(BaseIntegration):
    """Persist execution tasks to a Notion database."""

    name = "notion"
    action = "store_task"

    def __init__(self) -> None:
        self._settings = get_settings()

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != self.action:
            raise ValueError(f"Unsupported action for NotionAdapter: {action}")

        if not self._settings.notion_api_key:
            raise RuntimeError("NOTION_API_KEY is not configured")
        if not self._settings.notion_db_id:
            raise RuntimeError("NOTION_DB_ID is not configured")

        task = payload.get("task") or {}
        title = task.get("title") or task.get("task_id") or "Untitled task"
        description = task.get("description") or ""

        body: dict[str, Any] = {
            "parent": {"database_id": self._settings.notion_db_id},
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": title,
                            }
                        }
                    ]
                }
            },
        }

        if description:
            body["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": description,
                                },
                            }
                        ]
                    },
                }
            ]

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers={
                "Authorization": f"Bearer {self._settings.notion_api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=30,
        )
        response.raise_for_status()

        response_data = response.json()
        return {
            "integration": self.name,
            "action": action,
            "page_id": response_data.get("id"),
            "url": response_data.get("url"),
            "raw": response_data,
        }

