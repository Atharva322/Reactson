"""Implementation phase metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    index: int
    name: str
    status: str


PHASES: tuple[Phase, ...] = (
    Phase(0, "Reactson Foundation and Baseline", "completed"),
    Phase(1, "Epistemic Memory Foundation", "in_progress"),
    Phase(2, "Planning Framework and Complete MCTS", "pending"),
    Phase(3, "Execution, Tool Registry and MCP Synthesis", "pending"),
    Phase(4, "Kernel, API, Persistence and Observability", "pending"),
    Phase(5, "Real-World Engineering Agent", "pending"),
    Phase(6, "Evaluation, Reliability and Release Hardening", "pending"),
)
