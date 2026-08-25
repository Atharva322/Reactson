"""Benchmark datasets."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.planning.models import ActionCandidate


@dataclass(frozen=True)
class BenchmarkTask:
    task_id: str
    name: str
    start_state: str
    expected_action: str
    environment: object


class PlannerTrapEnvironment:
    def __init__(
        self,
        *,
        good_action: str = "boring_good",
        bad_action: str = "tempting_bad",
        good_prior: float = 0.0,
        bad_prior: float = 1.0,
    ) -> None:
        self.good_action = good_action
        self.bad_action = bad_action
        self.graph = {
            "start": {
                bad_action: "bad",
                good_action: "middle",
            },
            "middle": {"finish": "goal"},
            "bad": {"fail": "bad_terminal"},
        }
        self.rewards = {
            "start": 0.0,
            "middle": 0.25,
            "goal": 1.0,
            "bad": -0.25,
            "bad_terminal": -1.0,
        }
        self.priors = {
            bad_action: bad_prior,
            good_action: good_prior,
            "finish": 0.0,
            "fail": 0.0,
        }

    def actions(self, state, context, tools):
        return [
            ActionCandidate(name=name, prior_score=self.priors[name])
            for name in sorted(self.graph.get(state, {}))
        ]

    def transition(self, state, action):
        return self.graph[state][action.name]

    def reward(self, state):
        return self.rewards[state]

    def is_terminal(self, state):
        return state in {"goal", "bad_terminal"}


def default_planner_dataset() -> tuple[BenchmarkTask, ...]:
    return (
        BenchmarkTask(
            task_id="planner-trap-1",
            name="Prior trap",
            start_state="start",
            expected_action="boring_good",
            environment=PlannerTrapEnvironment(),
        ),
    )
