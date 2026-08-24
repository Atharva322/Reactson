"""Execution result critic."""

from __future__ import annotations

from dataclasses import dataclass, field

from reactson.execution.models import Action, ExecutionResult


@dataclass(frozen=True)
class ExecutionCritique:
    reward: float
    diagnosis: str
    signals: dict[str, float] = field(default_factory=dict)


class ExecutionCritic:
    def __init__(
        self,
        success_reward: float = 1.0,
        failure_penalty: float = 1.0,
        latency_penalty_per_second: float = 0.05,
        side_effect_penalty: float = 0.1,
    ) -> None:
        self.success_reward = success_reward
        self.failure_penalty = failure_penalty
        self.latency_penalty_per_second = latency_penalty_per_second
        self.side_effect_penalty = side_effect_penalty

    def evaluate(self, action: Action, result: ExecutionResult) -> ExecutionCritique:
        tool_signal = self.success_reward if result.success else -self.failure_penalty
        latency_penalty = (result.latency_ms / 1000) * self.latency_penalty_per_second
        side_effect_cost = len(result.side_effects) * self.side_effect_penalty
        reward = tool_signal - latency_penalty - side_effect_cost
        diagnosis = "tool_success" if result.success else "tool_failure"

        return ExecutionCritique(
            reward=reward,
            diagnosis=diagnosis,
            signals={
                "tool_success": 1.0 if result.success else 0.0,
                "tool_signal": tool_signal,
                "latency_penalty": latency_penalty,
                "side_effect_penalty": side_effect_cost,
                "expected_outcome_present": 1.0 if action.expected_outcome else 0.0,
            },
        )
