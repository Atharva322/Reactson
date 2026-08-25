"""Evidence-backed repository diagnosis agent."""

from __future__ import annotations

from pathlib import Path

from reactson.engineering.models import DiagnosisReport, Evidence, Hypothesis, Observation
from reactson.engineering.repository import RepositoryTools


class RepositoryDiagnosisAgent:
    def __init__(self, tools: RepositoryTools) -> None:
        self.tools = tools

    @classmethod
    def from_path(cls, root: str | Path) -> "RepositoryDiagnosisAgent":
        return cls(RepositoryTools(root))

    def diagnose(self, objective: str) -> DiagnosisReport:
        evidence = list(self.tools.collect_failure_files())
        evidence.extend(self.tools.search("failed", "*.py"))
        evidence.extend(self.tools.search("error", "*.py"))
        evidence.extend(self.tools.search("ImportError", "*.py"))
        evidence.extend(self.tools.search("AssertionError", "*.py"))

        observations = self._observations(tuple(evidence))
        hypotheses = self._hypotheses(tuple(evidence))
        summary = self._summary(objective, hypotheses)

        return DiagnosisReport(
            objective=objective,
            summary=summary,
            observations=observations,
            hypotheses=hypotheses,
            evidence=tuple(evidence),
            recommended_next_steps=(
                "Run the smallest failing test target first.",
                "Inspect the highest-confidence hypothesis evidence before patching.",
                "Add a regression test once the root cause is fixed.",
            ),
            metadata={"agent": "repository_diagnosis", "evidence_count": len(evidence)},
        )

    def _observations(self, evidence: tuple[Evidence, ...]) -> tuple[Observation, ...]:
        test_files = tuple(item for item in evidence if item.path and "test" in item.path.lower())
        error_lines = tuple(item for item in evidence if item.source == "code_search")
        return (
            Observation(summary=f"Found {len(test_files)} test-related files.", evidence=test_files),
            Observation(summary=f"Found {len(error_lines)} error/failure-related lines.", evidence=error_lines),
        )

    def _hypotheses(self, evidence: tuple[Evidence, ...]) -> tuple[Hypothesis, ...]:
        import_errors = tuple(item for item in evidence if "importerror" in item.detail.lower())
        assertions = tuple(item for item in evidence if "assertionerror" in item.detail.lower())
        generic_errors = tuple(item for item in evidence if "error" in item.detail.lower() or "failed" in item.detail.lower())

        hypotheses: list[Hypothesis] = []
        if import_errors:
            hypotheses.append(
                Hypothesis(
                    statement="A dependency or import compatibility issue may be causing the failure.",
                    confidence=0.85,
                    evidence=import_errors,
                )
            )
        if assertions:
            hypotheses.append(
                Hypothesis(
                    statement="A behavioral regression may be causing an assertion mismatch.",
                    confidence=0.75,
                    evidence=assertions,
                )
            )
        if generic_errors and not hypotheses:
            hypotheses.append(
                Hypothesis(
                    statement="The repository contains failure-related code or logs that should guide diagnosis.",
                    confidence=0.55,
                    evidence=generic_errors,
                )
            )
        if not hypotheses:
            hypotheses.append(
                Hypothesis(
                    statement="No direct failure markers were found; start by running the focused test suite.",
                    confidence=0.35,
                    evidence=evidence[:5],
                )
            )
        return tuple(hypotheses)

    def _summary(self, objective: str, hypotheses: tuple[Hypothesis, ...]) -> str:
        top = max(hypotheses, key=lambda item: item.confidence)
        return f"{objective}: {top.statement}"
