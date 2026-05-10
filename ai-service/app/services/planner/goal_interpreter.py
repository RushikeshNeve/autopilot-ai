"""Goal interpreter service."""

import time

from app.core.logger import get_logger
from app.rag.context import get_retrieved_context_text
from app.schemas.goal import GoalInterpretRequest, GoalInterpretResponse, InterpretedGoal
from app.rag.service import RAGService
from app.services.llm.client import LLMClient
from app.services.llm.prompts.goal_interpreter import build_goal_interpreter_prompt
from app.services.llm.structured_output import parse_structured_output

logger = get_logger(__name__)


class GoalInterpreterService:
    def __init__(self, rag_service: RAGService | None = None) -> None:
        self.llm_client = LLMClient()
        self.rag_service = rag_service or RAGService()

    def interpret_goal(self, request: GoalInterpretRequest) -> GoalInterpretResponse:
        start = time.perf_counter()
        logger.info(
            "goal_interpretation_started user_id=%s goal_text_length=%s constraints_count=%s",
            request.user_id,
            len(request.goal_text),
            len(request.constraints),
        )

        retrieved_context = get_retrieved_context_text(
            self.rag_service,
            query=self._build_retrieval_query(request),
            user_id=request.user_id,
            domain=request.domain_hint,
            top_k=3,
            max_chunks=3,
            max_chars=900,
        )

        prompt_start = time.perf_counter()
        prompt = build_goal_interpreter_prompt(request, retrieved_context=retrieved_context)
        logger.info(
            "goal_prompt_built user_id=%s prompt_chars=%s elapsed_ms=%.2f",
            request.user_id,
            len(prompt),
            (time.perf_counter() - prompt_start) * 1000,
        )

        llm_start = time.perf_counter()
        raw_output = self.llm_client.generate_text(prompt)
        logger.info(
            "goal_llm_response_received user_id=%s raw_output_chars=%s elapsed_ms=%.2f",
            request.user_id,
            len(raw_output),
            (time.perf_counter() - llm_start) * 1000,
        )

        parse_start = time.perf_counter()
        interpreted_goal = parse_structured_output(raw_output, InterpretedGoal)
        logger.info(
            "goal_output_parsed user_id=%s primary_intent=%s elapsed_ms=%.2f",
            request.user_id,
            interpreted_goal.primary_intent,
            (time.perf_counter() - parse_start) * 1000,
        )

        logger.info(
            "goal_interpretation_completed user_id=%s primary_intent=%s total_elapsed_ms=%.2f",
            request.user_id,
            interpreted_goal.primary_intent,
            (time.perf_counter() - start) * 1000,
        )

        return GoalInterpretResponse(
            user_id=request.user_id,
            interpreted_goal=interpreted_goal,
        )

    def _build_retrieval_query(self, request: GoalInterpretRequest) -> str:
        query_parts = [request.goal_text]
        if request.domain_hint:
            query_parts.append(f"domain_hint: {request.domain_hint}")
        if request.constraints:
            query_parts.append("constraints: " + "; ".join(request.constraints))
        return "\n".join(query_parts)
