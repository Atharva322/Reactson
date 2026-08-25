"""Non-destructive patch proposal helpers."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.engineering.models import DiagnosisReport, Evidence


@dataclass(frozen=True)
class PatchSuggestion:
    path: str
    rationale: str
    confidence: float
    proposed_change: str
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class PatchProposal:
    summary: str
    suggestions: tuple[PatchSuggestion, ...] = ()
    destructive: bool = False


class PatchProposalGenerator:
    def propose(self, report: DiagnosisReport) -> PatchProposal:
        top = max(report.hypotheses, key=lambda hypothesis: hypothesis.confidence)
        suggestions: list[PatchSuggestion] = []
        for evidence in top.evidence:
            if evidence.path is None:
                continue
            suggestions.append(
                PatchSuggestion(
                    path=evidence.path,
                    rationale=top.statement,
                    confidence=top.confidence,
                    proposed_change=_suggested_change(top.statement),
                    evidence=(evidence,),
                )
            )

        return PatchProposal(
            summary=f"Generated {len(suggestions)} non-destructive patch suggestions.",
            suggestions=tuple(_dedupe_by_path(suggestions)),
            destructive=False,
        )


def _suggested_change(statement: str) -> str:
    lowered = statement.lower()
    if "import" in lowered or "dependency" in lowered:
        return "Inspect imports and dependency declarations; update compatibility or dependency metadata."
    if "assertion" in lowered:
        return "Inspect the asserted behavior and update implementation or expectation with a regression test."
    return "Inspect the referenced failure evidence before making a minimal targeted change."


def _dedupe_by_path(suggestions: list[PatchSuggestion]) -> list[PatchSuggestion]:
    seen: set[str] = set()
    deduped: list[PatchSuggestion] = []
    for suggestion in suggestions:
        if suggestion.path in seen:
            continue
        deduped.append(suggestion)
        seen.add(suggestion.path)
    return deduped
