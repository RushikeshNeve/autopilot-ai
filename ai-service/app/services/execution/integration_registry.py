"""Registry for execution integrations."""

from __future__ import annotations

from threading import RLock
from typing import Any

from app.integrations.notion.notion_adapter import NotionAdapter
from app.integrations.generation.llm_generation_adapter import LLMGenerationAdapter
from app.integrations.notification.notification_adapter import NotificationAdapter
from app.integrations.scheduler.scheduler_adapter import SchedulerAdapter
from app.integrations.rag.rag_adapter import RAGAdapter
from app.services.execution.integration_base import BaseIntegration


class IntegrationRegistry:
    """Thread-safe registry mapping tool names to integration classes."""

    def __init__(self) -> None:
        self._integrations: dict[str, type[BaseIntegration]] = {}
        self._lock = RLock()

    def register(self, tool_name: str, integration_cls: type[BaseIntegration]) -> None:
        with self._lock:
            self._integrations[tool_name] = integration_cls

    def get_class(self, tool_name: str) -> type[BaseIntegration] | None:
        with self._lock:
            return self._integrations.get(tool_name)

    def get_instance(self, tool_name: str, **kwargs: Any) -> BaseIntegration:
        integration_cls = self.get_class(tool_name)
        if integration_cls is None:
            raise KeyError(f"No integration registered for tool_name='{tool_name}'")
        return integration_cls(**kwargs)


integration_registry = IntegrationRegistry()
integration_registry.register("notion", NotionAdapter)
integration_registry.register("notion_adapter", NotionAdapter)
integration_registry.register("rag_service", RAGAdapter)
integration_registry.register("rag_adapter", RAGAdapter)
integration_registry.register("rag", RAGAdapter)
integration_registry.register("llm_generation_service", LLMGenerationAdapter)
integration_registry.register("scheduler_adapter", SchedulerAdapter)
integration_registry.register("notification_adapter", NotificationAdapter)


def register_integration(tool_name: str, integration_cls: type[BaseIntegration]) -> None:
    integration_registry.register(tool_name, integration_cls)


def get_integration(tool_name: str, **kwargs: Any) -> BaseIntegration:
    return integration_registry.get_instance(tool_name, **kwargs)
