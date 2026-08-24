from __future__ import annotations

import asyncio

import pytest

from reactson.planning import ActionCandidate, HeuristicCritic, LinearPlanner, MCTSPlanner, PlanRequest, ReActPlanner
from reactson.planning.benchmark import run_planner_once
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


def test_react_planner_uses_environment_reasoned_action() -> None:
    planner = ReActPlanner(ReActEnvironment())

    result = asyncio.run(planner.propose(PlanRequest(state="start", context=("prefer explicit script",))))

    assert result.action is not None
    assert result.action.name == "scripted"
    assert result.metadata["thought"] == "script says scripted"


def test_mcts_budget_is_clamped_to_configured_simulation_limit() -> None:
    planner = MCTSPlanner(ToySearchEnvironment(), MCTSConfig(simulations=5, max_depth=3, random_seed=3))

    result = asyncio.run(planner.propose(PlanRequest(state="start", budget=100)))

    assert result.metadata["simulations"] == 5


def test_heuristic_critic_penalizes_repetition_and_invalid_actions() -> None:
    environment = NoOpEnvironment()
    critic = HeuristicCritic(environment)
    action = ActionCandidate(name="repeat")

    critique = critic.evaluate(
        state_before="same",
        action=action,
        state_after="same",
        seen_actions={(repr("same"), "repeat")},
    )

    assert critique.reward == pytest.approx(-1.25)
    assert critique.diagnosis == "invalid_or_noop_action"


def test_controlled_benchmark_shows_mcts_beats_linear_prior_trap() -> None:
    environment = PriorTrapEnvironment()
    linear = LinearPlanner(environment)
    mcts = MCTSPlanner(environment, MCTSConfig(simulations=20, max_depth=3, rollout_depth=2, random_seed=2))

    linear_result = run_planner_once(linear, PlanRequest(state="start"), "linear")
    mcts_result = run_planner_once(mcts, PlanRequest(state="start"), "mcts")

    assert linear_result.action == "tempting_bad"
    assert mcts_result.action == "boring_good"
    assert mcts_result.score > linear_result.score


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


class ReActEnvironment(PriorEnvironment):
    def actions(self, state, context, tools):
        return [
            ActionCandidate(name="fallback", prior_score=1.0),
            ActionCandidate(name="scripted", prior_score=0.1),
        ]

    def reason(self, state, context):
        return "script says scripted"

    def react_action(self, state):
        return "scripted"


class NoOpEnvironment:
    def actions(self, state, context, tools):
        return [ActionCandidate(name="repeat")]

    def transition(self, state, action):
        return state

    def reward(self, state):
        return 0.0

    def is_terminal(self, state):
        return False


class PriorTrapEnvironment:
    graph = {
        "start": {
            "tempting_bad": "bad",
            "boring_good": "middle",
        },
        "middle": {
            "finish": "goal",
        },
        "bad": {
            "fail": "bad_terminal",
        },
    }

    rewards = {
        "start": 0.0,
        "middle": 0.25,
        "goal": 1.0,
        "bad": -0.25,
        "bad_terminal": -1.0,
    }

    priors = {
        "tempting_bad": 1.0,
        "boring_good": 0.0,
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
