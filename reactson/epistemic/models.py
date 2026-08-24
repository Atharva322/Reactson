"""Typed memory models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ExecutionMemory:
    text: str
    task_id: str
    action: str | None = None
    result: str | None = None
    reward: float | None = None
    tags: tuple[str, ...] = ()
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphTriple:
    source: str
    relation: str
    target: str
    task_id: str
    evidence: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextItem:
    text: str
    source: str
    score: float
    task_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
