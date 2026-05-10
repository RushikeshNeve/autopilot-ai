"""LLM-backed content generation adapter."""

from __future__ import annotations

from typing import Any

from app.core.logger import get_logger
from app.services.execution.integration_base import BaseIntegration
from app.services.llm.client import LLMClient

logger = get_logger(__name__)


class LLMGenerationAdapter(BaseIntegration):
    """Generate structured content for execution tasks."""

    name = "llm_generation_service"
    action = "generate_content"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client or LLMClient()

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action != self.action:
            raise ValueError(f"Unsupported action for LLMGenerationAdapter: {action}")

        task = payload.get("task") or {}
        decision = payload.get("decision") or {}
        title = str(task.get("title") or "Untitled task")
        description = str(task.get("description") or "")
        task_id = str(task.get("task_id") or "")

        prompt = self._build_prompt(title=title, description=description, decision=decision, task_id=task_id)
        generated_text = self._generate(prompt, title=title, description=description)

        return {
            "integration": self.name,
            "action": action,
            "task_id": task_id,
            "tool_category": decision.get("tool_category"),
            "generated_content": generated_text,
            "format": "markdown",
        }

    def _generate(self, prompt: str, *, title: str, description: str) -> str:
        if self._llm_client.client is None:
            logger.info("llm_generation_fallback mode=deterministic")
            return (
                f"# {title}\n\n"
                f"## Summary\n{description or 'No description provided.'}\n\n"
                "## Next steps\n"
                "- Review the generated draft.\n"
                "- Adapt it to the task constraints.\n"
                "- Save the output to the plan or knowledge base.\n"
            )

        try:
            return self._llm_client.generate_text(prompt)
        except Exception as exc:
            logger.warning("llm_generation_failed error=%s", exc)
            return (
                f"# {title}\n\n"
                f"## Summary\n{description or 'No description provided.'}\n\n"
                "## Next steps\n"
                "- Review the generated draft.\n"
                "- Adapt it to the task constraints.\n"
                "- Save the output to the plan or knowledge base.\n"
            )

    def _build_prompt(self, *, title: str, description: str, decision: dict[str, Any], task_id: str) -> str:
        return (
            "Generate concise, actionable content for an execution task.\n"
            f"Task ID: {task_id}\n"
            f"Task title: {title}\n"
            f"Task description: {description}\n"
            f"Routing decision: {decision}\n"
            "Return markdown with sections for Summary, Deliverable, and Next steps."
        )
