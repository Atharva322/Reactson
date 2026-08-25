"""API schema helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reactson.core.events import TaskEvent
from reactson.core.session import TaskSession


@dataclass(frozen=True)
class CreateTaskRequest:
    objective: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunTaskRequest:
    budget: int | None = None


def task_payload(session: TaskSession) -> dict[str, Any]:
    return session.to_dict()


def event_payload(event: TaskEvent) -> dict[str, Any]:
    return event.to_dict()
