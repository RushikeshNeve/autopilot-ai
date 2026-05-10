"""Milestone planner service."""

from pydantic import BaseModel
from app.core.logger import get_logger
from app.rag.context import get_retrieved_context_text
from app.schemas.goal import InterpretedGoal
from app.schemas.plan import MilestonePlanResponse
from app.schemas.task import Milestone
from app.rag.service import RAGService
from app.services.llm.client import LLMClient
from app.services.llm.structured_output import parse_structured_output
from app.services.llm.prompts.milestone_planner import build_milestone_planner_prompt

logger = get_logger(__name__)


class MilestonePlannerOutput(BaseModel):
    milestones: list[Milestone]


class MilestonePlannerService:
    def __init__(self, rag_service: RAGService | None = None) -> None:
        self.llm_client = LLMClient()
        self.rag_service = rag_service or RAGService()

    def generate_milestones(
        self,
        user_id: str,
        interpreted_goal: InterpretedGoal,
    ) -> MilestonePlanResponse:
        logger.info("Generating milestones for user_id=%s", user_id)

        retrieved_context = get_retrieved_context_text(
            self.rag_service,
            query=self._build_retrieval_query(interpreted_goal),
            user_id=user_id,
            domain=interpreted_goal.domain,
            top_k=4,
            max_chunks=4,
            max_chars=1000,
        )
        prompt = build_milestone_planner_prompt(
            user_id,
            interpreted_goal,
            retrieved_context=retrieved_context,
        )
        raw_output = self.llm_client.generate_text(prompt)
        parsed = parse_structured_output(raw_output, MilestonePlannerOutput)

        logger.info(
            "Generated %s milestones for user_id=%s",
            len(parsed.milestones),
            user_id,
        )

        return MilestonePlanResponse(
            user_id=user_id,
            interpreted_goal=interpreted_goal,
            milestones=parsed.milestones,
        )

    def _build_retrieval_query(self, interpreted_goal: InterpretedGoal) -> str:
        return " ".join(
            part
            for part in [
                interpreted_goal.primary_intent,
                interpreted_goal.domain,
                ", ".join(interpreted_goal.target_outcomes),
            ]
            if part
        )
