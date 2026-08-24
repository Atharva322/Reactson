"""Controlled planner benchmark helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from reactson.planning.base import PlanningStrategy
from reactson.planning.models import PlanRequest


@dataclass(frozen=True)
class PlannerBenchmarkResult:
    planner: str
    action: str | None
    score: float
    nodes_expanded: int = 0
    simulations: int = 0


def run_planner_once(planner: PlanningStrategy, request: PlanRequest, name: str) -> PlannerBenchmarkResult:
    result = asyncio.run(planner.propose(request))
    score = result.score
    if result.action is not None and hasattr(planner, "environment"):
        environment = planner.environment
        next_state = environment.transition(request.state, result.action)
        score = float(environment.reward(next_state))

    return PlannerBenchmarkResult(
        planner=name,
        action=result.action.name if result.action else None,
        score=score,
        nodes_expanded=int(result.metadata.get("nodes_expanded", 0)),
        simulations=int(result.metadata.get("simulations", 0)),
    )
