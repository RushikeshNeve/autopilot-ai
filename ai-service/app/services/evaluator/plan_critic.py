"""Plan critic service."""

from app.core.logger import get_logger
from app.rag.context import get_retrieved_context_text
from app.rag.service import RAGService
from app.services.llm.client import LLMClient
from app.services.llm.structured_output import parse_structured_output
from app.services.llm.prompts.critic import build_plan_critic_prompt
from app.schemas.evaluation import PlanCritique

logger = get_logger(__name__)


class PlanCriticService:
    def __init__(self, rag_service: RAGService | None = None) -> None:
        self.llm_client = LLMClient()
        self.rag_service = rag_service or RAGService()

    def critique_plan(self, user_id: str, plan: dict) -> PlanCritique:
        logger.info("Critiquing plan for user_id=%s", user_id)

        retrieved_context = get_retrieved_context_text(
            self.rag_service,
            query=self._build_retrieval_query(plan),
            user_id=user_id,
            top_k=3,
            max_chunks=3,
            max_chars=900,
        )
        prompt = build_plan_critic_prompt(user_id, str(plan), retrieved_context=retrieved_context)
        raw_output = self.llm_client.generate_text(prompt)

        critique = parse_structured_output(raw_output, PlanCritique)

        logger.info(
            "Critique completed with score=%s issue_count=%s for user_id=%s",
            critique.overall_score,
            len(critique.issues),
            user_id,
        )

        return critique

    def _build_retrieval_query(self, plan: dict) -> str:
        return str(plan)
