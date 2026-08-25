"""Hypothesis and evidence tracking for engineering diagnosis."""

from __future__ import annotations

from dataclasses import dataclass, field

from reactson.engineering.models import Evidence, Hypothesis, Observation


@dataclass
class DiagnosisSession:
    evidence: list[Evidence] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)

    def add_evidence(self, items: tuple[Evidence, ...]) -> None:
        seen = {(item.source, item.detail, item.path, item.line) for item in self.evidence}
        for item in items:
            key = (item.source, item.detail, item.path, item.line)
            if key not in seen:
                self.evidence.append(item)
                seen.add(key)

    def add_observations(self, items: tuple[Observation, ...]) -> None:
        self.observations.extend(items)

    def set_hypotheses(self, items: tuple[Hypothesis, ...]) -> None:
        self.hypotheses = sorted(items, key=lambda hypothesis: hypothesis.confidence, reverse=True)
