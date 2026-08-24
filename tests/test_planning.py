from __future__ import annotations

import asyncio

import pytest

from reactson.planning import ActionCandidate, LinearPlanner, MCTSPlanner, PlanRequest
from reactson.planning.mcts import MCTSConfig


def test_linear_planner_selects_highest_prior_action() -> None:
    planner = LinearPlanner(PriorEnvironment())

    result = asyncio.run(planner.propose(PlanRequest(state="start")))

    assert result.action is not None
    assert result.action.name == "best_prior"
    assert result.metadata["candidate_count"] == 2


def test_mcts_solves_deterministic_toy_search() -> None:
    planner = MCTSPlanner(
        ToySearchEnvironment(),
        MCTSConfig(simulations=24, max_depth=3, rollout_depth=2, random_seed=7),
    )

    result = asyncio.run(planner.propose(PlanRequest(state="start")))

    assert result.action is not None
    assert result.action.name == "toward_goal"
    assert result.score == pytest.approx(1.0)
    assert result.metadata["simulations"] == 24
    assert result.metadata["nodes_expanded"] >= 3
    assert result.metadata["tree"]["children"]


def test_mcts_returns_no_action_for_terminal_root() -> None:
    planner = MCTSPlanner(ToySearchEnvironment(), MCTSConfig(simulations=4, random_seed=1))

    result = asyncio.run(planner.propose(PlanRequest(state="goal")))

    assert result.action is None
    assert result.score == pytest.approx(1.0)


class PriorEnvironment:
    def actions(self, state, context, tools):
        return [
            ActionCandidate(name="low_prior", prior_score=0.1),
            ActionCandidate(name="best_prior", prior_score=0.8),
        ]

    def transition(self, state, action):
        return action.name

    def reward(self, state):
        return 0.0

    def is_terminal(self, state):
        return False


class ToySearchEnvironment:
    graph = {
        "start": {
            "toward_goal": "middle",
            "dead_end": "bad",
        },
        "middle": {
            "finish": "goal",
        },
        "bad": {
            "stay_bad": "bad_terminal",
        },
    }

    rewards = {
        "goal": 1.0,
        "middle": 0.5,
        "start": 0.0,
        "bad": -0.2,
        "bad_terminal": -1.0,
    }

    def actions(self, state, context, tools):
        return [
            ActionCandidate(name=name, prior_score=0.0)
            for name in sorted(self.graph.get(state, {}))
        ]

    def transition(self, state, action):
        return self.graph[state][action.name]

    def reward(self, state):
        return self.rewards[state]

    def is_terminal(self, state):
        return state in {"goal", "bad_terminal"}
