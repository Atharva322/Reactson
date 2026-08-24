"""Typed execution models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Action:
    type: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    expected_outcome: str = ""


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    output: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    side_effects: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
