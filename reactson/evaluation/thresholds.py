"""Regression thresholds for benchmark smoke tests."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.evaluation.metrics import EvaluationSummary


@dataclass(frozen=True)
class RegressionThreshold:
    planner: str
    minimum_completion_rate: float


def assert_thresholds(summary: EvaluationSummary, thresholds: tuple[RegressionThreshold, ...]) -> None:
    by_planner = {metric.planner: metric for metric in summary.planner_metrics}
    failures: list[str] = []
    for threshold in thresholds:
        metric = by_planner.get(threshold.planner)
        if metric is None:
            failures.append(f"missing metrics for planner {threshold.planner}")
            continue
        if metric.completion_rate < threshold.minimum_completion_rate:
            failures.append(
                f"{threshold.planner} completion {metric.completion_rate:.2f} "
                f"< {threshold.minimum_completion_rate:.2f}"
            )
    if failures:
        raise AssertionError("; ".join(failures))
