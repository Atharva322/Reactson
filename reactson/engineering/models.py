"""Engineering diagnosis models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Evidence:
    source: str
    detail: str
    path: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class Observation:
    summary: str
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class Hypothesis:
    statement: str
    confidence: float
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class DiagnosisReport:
    objective: str
    summary: str
    observations: tuple[Observation, ...] = ()
    hypotheses: tuple[Hypothesis, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    recommended_next_steps: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)

    def final_answer(self) -> str:
        lines = [self.summary]
        if self.hypotheses:
            top = max(self.hypotheses, key=lambda hypothesis: hypothesis.confidence)
            lines.append(f"Top hypothesis ({top.confidence:.2f}): {top.statement}")
        if self.evidence:
            lines.append("Evidence:")
            for item in self.evidence[:5]:
                location = f" ({item.path}:{item.line})" if item.path and item.line else f" ({item.path})" if item.path else ""
                lines.append(f"- {item.source}{location}: {item.detail}")
        if self.recommended_next_steps:
            lines.append("Next steps:")
            for step in self.recommended_next_steps:
                lines.append(f"- {step}")
        return "\n".join(lines)


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
