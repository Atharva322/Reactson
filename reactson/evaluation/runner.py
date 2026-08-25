"""Evaluation runner."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from reactson.evaluation.datasets import BenchmarkTask
from reactson.planning import LinearPlanner, MCTSPlanner, PlanRequest, ReActPlanner
from reactson.planning.benchmark import run_planner_once
from reactson.planning.mcts import MCTSConfig


PlannerFactory = Callable[[object], object]


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    task_name: str
    planner: str
    action: str | None
    expected_action: str
    score: float
    success: bool
    latency_ms: float
    nodes_expanded: int
    simulations: int


class EvaluationRunner:
    def __init__(self, planner_factories: dict[str, PlannerFactory] | None = None) -> None:
        self.planner_factories = planner_factories or {
            "linear": lambda environment: LinearPlanner(environment),
            "react": lambda environment: ReActPlanner(environment),
            "mcts": lambda environment: MCTSPlanner(
                environment,
                MCTSConfig(simulations=20, max_depth=3, rollout_depth=2, random_seed=2),
            ),
        }

    def run(self, tasks: tuple[BenchmarkTask, ...]) -> tuple[EvaluationResult, ...]:
        results: list[EvaluationResult] = []
        for task in tasks:
            for planner_name, factory in self.planner_factories.items():
                planner = factory(task.environment)
                started = perf_counter()
                benchmark = run_planner_once(planner, PlanRequest(state=task.start_state), planner_name)
                latency_ms = (perf_counter() - started) * 1000
                results.append(
                    EvaluationResult(
                        task_id=task.task_id,
                        task_name=task.name,
                        planner=planner_name,
                        action=benchmark.action,
                        expected_action=task.expected_action,
                        score=benchmark.score,
                        success=benchmark.action == task.expected_action,
                        latency_ms=latency_ms,
                        nodes_expanded=benchmark.nodes_expanded,
                        simulations=benchmark.simulations,
                    )
                )
        return tuple(results)
