"""Execution routing service."""

from __future__ import annotations

import time

from app.core.logger import get_logger
from pydantic import BaseModel

from app.schemas.execution import ExecutionDecision, ExecutionResponse
from app.schemas.task import TaskItem
from app.services.llm.client import LLMClient
from app.services.llm.prompts.execution_router import build_execution_router_prompt
from app.services.llm.structured_output import StructuredOutputError, parse_structured_output

logger = get_logger(__name__)


class ExecutionRouterOutput(BaseModel):
    """Structured output returned by the execution router prompt."""

    decisions: list[ExecutionDecision]


class ExecutionRouterService:
    """Classify tasks into execution decisions using the LLM router prompt."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def route_tasks(self, user_id: str, tasks: list[TaskItem]) -> ExecutionResponse:
        start = time.perf_counter()
        logger.info("execution_routing_started user_id=%s tasks_count=%s", user_id, len(tasks))

        if len(tasks) > 12:
            logger.info("execution_routing_deterministic_fallback user_id=%s tasks_count=%s", user_id, len(tasks))
            decisions = self._route_tasks_deterministically(tasks)
            return self._build_response(user_id=user_id, decisions=decisions, start=start)

        tasks_json = self._build_tasks_json(tasks)
        prompt = build_execution_router_prompt(user_id=user_id, tasks_json=tasks_json)
        try:
            raw_output = self.llm_client.generate_text(prompt)
            parsed = parse_structured_output(raw_output, ExecutionRouterOutput)
            decisions = parsed.decisions
        except StructuredOutputError as exc:
            logger.warning("execution_routing_llm_fallback user_id=%s error=%s", user_id, exc)
            decisions = self._route_tasks_deterministically(tasks)

        return self._build_response(user_id=user_id, decisions=decisions, start=start)

    def _build_response(self, user_id: str, decisions: list[ExecutionDecision], start: float) -> ExecutionResponse:
        logger.info(
            "execution_routing_completed user_id=%s decisions_count=%s elapsed_ms=%.2f",
            user_id,
            len(decisions),
            (time.perf_counter() - start) * 1000,
        )

        return ExecutionResponse(user_id=user_id, decisions=decisions)

    def _build_tasks_json(self, tasks: list[TaskItem]) -> str:
        compact_tasks = [self._task_summary(task) for task in tasks]
        return "[" + ",\n".join(task.model_dump_json(indent=2) for task in compact_tasks) + "]"

    def _task_summary(self, task: TaskItem) -> TaskItem:
        return TaskItem(
            task_id=task.task_id,
            milestone_id=task.milestone_id,
            title=task.title,
            description=(task.description[:240] if task.description else ""),
            task_type=task.task_type,
            priority=task.priority,
            estimated_minutes=task.estimated_minutes,
            dependencies=task.dependencies,
            requires_approval=task.requires_approval,
            suggested_tools=task.suggested_tools[:3],
        )

    def _route_tasks_deterministically(self, tasks: list[TaskItem]) -> list[ExecutionDecision]:
        decisions: list[ExecutionDecision] = []
        for task in tasks:
            action_mode, tool_category, reason, confidence = self._decide_task(task)
            decisions.append(
                ExecutionDecision(
                    task_id=task.task_id,
                    action_mode=action_mode,
                    tool_category=tool_category,
                    tool_name=None,
                    domain=None,
                    reason=reason,
                    confidence=confidence,
                )
            )
        return decisions

    def _decide_task(self, task: TaskItem) -> tuple[str, str | None, str, float]:
        title = task.title.lower()
        description = (task.description or "").lower()
        combined = f"{title} {description}"

        if task.requires_approval:
            return (
                "requires_approval",
                self._infer_tool_category(task),
                "Task is marked as requiring approval before execution.",
                0.95,
            )

        tool_category = self._infer_tool_category(task)
        if tool_category is None:
            return (
                "suggest",
                None,
                "Task is useful but not clearly tied to an execution capability, so it is suggested to the user.",
                0.72,
            )

        if "notify" in combined or tool_category == "notify":
            return (
                "requires_approval",
                "notify",
                "Outbound communication should be confirmed by the user before sending.",
                0.94,
            )

        if tool_category == "store_data" and ("export" in combined or "save" in combined or "compile" in combined):
            return (
                "auto_execute",
                tool_category,
                "The task is a safe storage or compilation step that can run automatically.",
                0.9,
            )

        return (
            "auto_execute",
            tool_category,
            "The task is a safe content or knowledge operation that can run automatically.",
            0.87,
        )

    def _infer_tool_category(self, task: TaskItem) -> str | None:
        text = f"{task.title} {task.description or ''} {task.task_type}".lower()
        if any(keyword in text for keyword in ["schedule", "calendar", "reminder"]):
            return "schedule"
        if any(keyword in text for keyword in ["notify", "email", "message", "send"]):
            return "notify"
        if any(keyword in text for keyword in ["store", "save", "export", "compile", "assemble"]):
            return "store_data"
        if any(keyword in text for keyword in ["extract", "identify", "index", "research", "review", "retrieve"]):
            return "retrieve_knowledge"
        if any(keyword in text for keyword in ["draft", "write", "generate", "plan", "design", "document"]):
            return "generate_content"
        if task.task_type in {"planning", "drafting"}:
            return "generate_content"
        if task.task_type in {"study", "review"}:
            return "retrieve_knowledge"
        if task.task_type == "execution":
            return "generate_content"
        return None
