"""Release checklist helpers."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.evaluation.docs import DocumentationCheckResult
from reactson.evaluation.metrics import EvaluationSummary
from reactson.evaluation.security import SecurityCheckResult


@dataclass(frozen=True)
class ReleaseChecklist:
    items: tuple[str, ...]
    ready: bool


def build_release_checklist(
    summary: EvaluationSummary,
    security: tuple[SecurityCheckResult, ...],
    docs: tuple[DocumentationCheckResult, ...],
) -> ReleaseChecklist:
    items: list[str] = []
    items.append("planner evaluation metrics generated")
    items.append("security checks passed" if all(item.passed for item in security) else "security checks failing")
    items.append("documentation checks passed" if all(item.passed for item in docs) else "documentation checks failing")
    items.append(f"planner metrics count: {len(summary.planner_metrics)}")
    ready = all(item.passed for item in security) and all(item.passed for item in docs) and bool(summary.planner_metrics)
    return ReleaseChecklist(items=tuple(items), ready=ready)
