"""Evaluation report rendering."""

from __future__ import annotations

import json

from reactson.evaluation.metrics import EvaluationSummary
from reactson.evaluation.runner import EvaluationResult


def render_json_report(results: tuple[EvaluationResult, ...], summary: EvaluationSummary) -> str:
    return json.dumps(
        {
            "results": [result.__dict__ for result in results],
            "summary": {"planner_metrics": [metric.__dict__ for metric in summary.planner_metrics]},
        },
        indent=2,
        sort_keys=True,
    )


def render_html_report(results: tuple[EvaluationResult, ...], summary: EvaluationSummary) -> str:
    rows = "\n".join(
        f"<tr><td>{metric.planner}</td><td>{metric.completion_rate:.2f}</td><td>{metric.average_score:.2f}</td></tr>"
        for metric in summary.planner_metrics
    )
    return (
        "<html><body><h1>Reactson Evaluation Report</h1>"
        "<table><tr><th>Planner</th><th>Completion</th><th>Average Score</th></tr>"
        f"{rows}</table><p>Runs: {len(results)}</p></body></html>"
    )
