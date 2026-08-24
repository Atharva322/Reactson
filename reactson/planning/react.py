"""ReAct-style planning baseline."""

from __future__ import annotations

from reactson.planning.base import PlanningStrategy
from reactson.planning.models import ActionCandidate, PlanRequest, PlanResult, PlanningEnvironment, Transition


class ReActPlanner(PlanningStrategy):
    def __init__(self, environment: PlanningEnvironment) -> None:
        self.environment = environment
        self.transitions: list[Transition] = []

    async def propose(self, request: PlanRequest) -> PlanResult:
        thought = self._thought(request)
        actions = self.environment.actions(request.state, request.context, request.tools)
        if not actions:
            return PlanResult(action=None, score=0.0, metadata={"planner": "react", "thought": thought})

        scripted_action = self._scripted_action(request.state, actions)
        action = scripted_action or max(actions, key=lambda candidate: (candidate.prior_score, candidate.name))
        return PlanResult(
            action=action,
            score=action.prior_score,
            metadata={"planner": "react", "thought": thought, "candidate_count": len(actions)},
        )

    async def update(self, transition: Transition) -> None:
        self.transitions.append(transition)

    def _thought(self, request: PlanRequest) -> str:
        if hasattr(self.environment, "reason"):
            return str(self.environment.reason(request.state, request.context))
        if request.context:
            return request.context[-1]
        return f"choose next action for {request.state!r}"

    def _scripted_action(self, state, actions: list[ActionCandidate]) -> ActionCandidate | None:
        if not hasattr(self.environment, "react_action"):
            return None
        action_name = self.environment.react_action(state)
        for action in actions:
            if action.name == action_name:
                return action
        return None
