"""Linear planning baseline."""

from __future__ import annotations

from reactson.planning.base import PlanningStrategy
from reactson.planning.models import PlanRequest, PlanResult, PlanningEnvironment, Transition


class LinearPlanner(PlanningStrategy):
    def __init__(self, environment: PlanningEnvironment) -> None:
        self.environment = environment
        self.transitions: list[Transition] = []

    async def propose(self, request: PlanRequest) -> PlanResult:
        actions = self.environment.actions(request.state, request.context, request.tools)
        if not actions:
            return PlanResult(action=None, score=0.0, metadata={"planner": "linear"})

        action = max(actions, key=lambda candidate: candidate.prior_score)
        return PlanResult(
            action=action,
            score=action.prior_score,
            metadata={"planner": "linear", "candidate_count": len(actions)},
        )

    async def update(self, transition: Transition) -> None:
        self.transitions.append(transition)
