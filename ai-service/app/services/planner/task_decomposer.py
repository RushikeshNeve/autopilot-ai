"""Task decomposition service."""

from pydantic import BaseModel
from app.core.logger import get_logger
from app.rag.context import get_retrieved_context_text
from app.schemas.goal import InterpretedGoal
from app.schemas.plan import TaskPlanResponse
from app.schemas.task import Milestone, TaskItem
from app.rag.service import RAGService
from app.services.llm.client import LLMClient
from app.services.llm.structured_output import parse_structured_output
from app.services.llm.prompts.task_planner import build_task_planner_prompt

logger = get_logger(__name__)


class TaskPlannerOutput(BaseModel):
    tasks: list[TaskItem]


class TaskDecomposerService:
    def __init__(self, rag_service: RAGService | None = None) -> None:
        self.llm_client = LLMClient()
        self.rag_service = rag_service or RAGService()

    def generate_tasks_for_milestone(
        self,
        user_id: str,
        interpreted_goal: InterpretedGoal,
        milestone: Milestone,
    ) -> TaskPlanResponse:
        logger.info(
            "Generating tasks for user_id=%s milestone_id=%s",
            user_id,
            milestone.milestone_id,
        )

        retrieved_context = get_retrieved_context_text(
            self.rag_service,
            query=self._build_retrieval_query(interpreted_goal, milestone),
            user_id=user_id,
            domain=interpreted_goal.domain,
            top_k=3,
            max_chunks=3,
            max_chars=800,
        )
        prompt = build_task_planner_prompt(
            user_id=user_id,
            interpreted_goal=interpreted_goal,
            milestone=milestone,
            retrieved_context=retrieved_context,
        )
        raw_output = self.llm_client.generate_text(prompt)
        parsed = parse_structured_output(raw_output, TaskPlannerOutput)

        logger.info(
            "Generated %s tasks for milestone_id=%s",
            len(parsed.tasks),
            milestone.milestone_id,
        )

        return TaskPlanResponse(
            user_id=user_id,
            milestone=milestone,
            tasks=parsed.tasks,
        )

    def _build_retrieval_query(self, interpreted_goal: InterpretedGoal, milestone: Milestone) -> str:
        return " ".join(
            part
            for part in [
                interpreted_goal.primary_intent,
                interpreted_goal.domain,
                milestone.title,
                milestone.description,
            ]
            if part
        )
