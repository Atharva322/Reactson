"""Deterministic planning critic helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reactson.planning.models import ActionCandidate, PlanningEnvironment


@dataclass(frozen=True)
class Critique:
    reward: float
    diagnosis: str
    signals: dict[str, float] = field(default_factory=dict)


class HeuristicCritic:
    def __init__(
        self,
        environment: PlanningEnvironment,
        repetition_penalty: float = 0.25,
        invalid_action_penalty: float = 1.0,
    ) -> None:
        self.environment = environment
        self.repetition_penalty = repetition_penalty
        self.invalid_action_penalty = invalid_action_penalty

    def evaluate(
        self,
        *,
        state_before: Any,
        action: ActionCandidate,
        state_after: Any,
        seen_actions: set[tuple[str, str]] | None = None,
    ) -> Critique:
        base_reward = self.environment.reward(state_after)
        repeated = (repr(state_before), action.name) in (seen_actions or set())
        invalid = state_before == state_after and not self.environment.is_terminal(state_after)

        reward = base_reward
        reward -= self.repetition_penalty if repeated else 0.0
        reward -= self.invalid_action_penalty if invalid else 0.0

        diagnosis = "progress"
        if invalid:
            diagnosis = "invalid_or_noop_action"
        elif repeated:
            diagnosis = "repeated_action"
        elif self.environment.is_terminal(state_after):
            diagnosis = "terminal_state"

        return Critique(
            reward=reward,
            diagnosis=diagnosis,
            signals={
                "base_reward": base_reward,
                "repetition_penalty": self.repetition_penalty if repeated else 0.0,
                "invalid_action_penalty": self.invalid_action_penalty if invalid else 0.0,
            },
        )
