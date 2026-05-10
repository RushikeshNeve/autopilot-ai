"""Plan reviser service."""
from app.core.logger import get_logger
from app.services.llm.client import LLMClient
from app.services.llm.structured_output import parse_structured_output
from app.services.llm.prompts.plan_reviser import build_plan_reviser_prompt
from app.schemas.plan import FinalizedPlan

logger = get_logger(__name__)


class PlanReviserService:
    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def revise_plan(self, plan: FinalizedPlan, critique: dict) -> FinalizedPlan:
        logger.info("Revising plan based on critique")

        prompt = build_plan_reviser_prompt(
            plan_json=plan.model_dump_json(indent=2),
            critique_json=str(critique),
        )

        raw_output = self.llm_client.generate_text(prompt)
        revised_plan = parse_structured_output(raw_output, FinalizedPlan)

        logger.info("Plan revision completed")

        return revised_plan