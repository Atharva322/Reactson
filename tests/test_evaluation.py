from __future__ import annotations

import json

import pytest

from reactson.evaluation import EvaluationRunner, default_planner_dataset, render_html_report, render_json_report
from reactson.evaluation.metrics import summarize_results
from reactson.evaluation.thresholds import RegressionThreshold, assert_thresholds


def test_evaluation_runner_compares_planners_on_same_task() -> None:
    results = EvaluationRunner().run(default_planner_dataset())
    by_planner = {result.planner: result for result in results}

    assert set(by_planner) == {"linear", "react", "mcts"}
    assert by_planner["mcts"].success is True
    assert by_planner["mcts"].score > by_planner["linear"].score
    assert by_planner["mcts"].simulations == 20


def test_evaluation_summary_and_reports_are_reproducible() -> None:
    results = EvaluationRunner().run(default_planner_dataset())
    summary = summarize_results(results)
    json_report = render_json_report(results, summary)
    html_report = render_html_report(results, summary)

    parsed = json.loads(json_report)

    assert parsed["summary"]["planner_metrics"]
    assert "Reactson Evaluation Report" in html_report
    assert any(metric.planner == "mcts" and metric.completion_rate == 1.0 for metric in summary.planner_metrics)


def test_regression_thresholds_fail_when_planner_drops_below_gate() -> None:
    results = EvaluationRunner().run(default_planner_dataset())
    summary = summarize_results(results)

    assert_thresholds(summary, (RegressionThreshold(planner="mcts", minimum_completion_rate=1.0),))
    with pytest.raises(AssertionError):
        assert_thresholds(summary, (RegressionThreshold(planner="linear", minimum_completion_rate=1.0),))
