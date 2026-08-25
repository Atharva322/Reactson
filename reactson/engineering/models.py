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


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
