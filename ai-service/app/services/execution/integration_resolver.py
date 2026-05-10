"""Capability to integration routing for the execution layer."""

from __future__ import annotations


class IntegrationResolver:
    """Resolve abstract capabilities to concrete integration tool names."""

    _CAPABILITY_TO_TOOL_NAME: dict[str, str] = {
        "retrieve_knowledge": "rag_service",
        "store_data": "notion_adapter",
        "schedule": "scheduler_adapter",
        "notify": "notification_adapter",
        "generate_content": "llm_generation_service",
    }

    def resolve(self, capability: str, domain: str | None = None) -> str | None:
        """Resolve a capability to a tool name.

        The `domain` argument is reserved for future specialization and is not
        used yet.
        """
        return self._CAPABILITY_TO_TOOL_NAME.get(capability)
