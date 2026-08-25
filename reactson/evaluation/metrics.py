"""Evaluation metrics."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.evaluation.runner import EvaluationResult


@dataclass(frozen=True)
class PlannerMetrics:
    planner: str
    task_count: int
    completion_rate: float
    average_score: float
    average_latency_ms: float
    total_nodes_expanded: int
    total_simulations: int


@dataclass(frozen=True)
class EvaluationSummary:
    planner_metrics: tuple[PlannerMetrics, ...]


def summarize_results(results: tuple[EvaluationResult, ...]) -> EvaluationSummary:
    planners = sorted({result.planner for result in results})
    metrics: list[PlannerMetrics] = []
    for planner in planners:
        selected = [result for result in results if result.planner == planner]
        task_count = len(selected)
        metrics.append(
            PlannerMetrics(
                planner=planner,
                task_count=task_count,
                completion_rate=sum(1 for result in selected if result.success) / task_count if task_count else 0.0,
                average_score=sum(result.score for result in selected) / task_count if task_count else 0.0,
                average_latency_ms=sum(result.latency_ms for result in selected) / task_count if task_count else 0.0,
                total_nodes_expanded=sum(result.nodes_expanded for result in selected),
                total_simulations=sum(result.simulations for result in selected),
            )
        )
    return EvaluationSummary(planner_metrics=tuple(metrics))
