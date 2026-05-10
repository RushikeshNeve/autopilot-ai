"""Plan finalization service."""

from app.schemas.goal import InterpretedGoal
from app.schemas.plan import FinalizedPlan
from app.schemas.task import Milestone, TaskItem


class PlanFinalizerService:
    def finalize_plan(
        self,
        user_id: str,
        interpreted_goal: InterpretedGoal,
        milestones: list[Milestone],
        tasks: list[TaskItem],
    ) -> FinalizedPlan:
        assumptions = self._build_assumptions(interpreted_goal)
        risks = self._build_risks(interpreted_goal)
        next_best_action = self._select_next_best_action(tasks)

        return FinalizedPlan(
            user_id=user_id,
            interpreted_goal=interpreted_goal,
            milestones=milestones,
            tasks=tasks,
            assumptions=assumptions,
            risks=risks,
            next_best_action=next_best_action,
        )

    def _build_assumptions(self, interpreted_goal: InterpretedGoal) -> list[str]:
        assumptions = []

        if interpreted_goal.estimated_horizon:
            assumptions.append(
                f"Plan assumes a working horizon of {interpreted_goal.estimated_horizon}."
            )

        if interpreted_goal.constraints:
            assumptions.append("Plan is shaped around the provided constraints.")

        if not assumptions:
            assumptions.append("Plan assumes normal execution capacity and stable availability.")

        return assumptions

    def _build_risks(self, interpreted_goal: InterpretedGoal) -> list[str]:
        risks = []

        if "burnout" in " ".join(interpreted_goal.constraints).lower():
            risks.append("Overloading the schedule may reduce consistency and execution quality.")

        if interpreted_goal.urgency == "high":
            risks.append("High urgency may compress milestones and reduce execution quality.")

        if not risks:
            risks.append("Execution consistency is the main risk for successful completion.")

        return risks

    def _select_next_best_action(self, tasks: list[TaskItem]) -> str:
        if not tasks:
            return "No actionable task generated yet."

        sorted_tasks = sorted(
            tasks,
            key=lambda task: (
                0 if task.priority == "high" else 1 if task.priority == "medium" else 2,
                task.estimated_minutes or 9999,
            ),
        )
        return sorted_tasks[0].title