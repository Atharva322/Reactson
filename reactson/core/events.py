"""Task event models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class TaskEvent:
    task_id: str
    type: str
    message: str
    trace_id: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "task_id": self.task_id,
            "type": self.type,
            "message": self.message,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskEvent":
        return cls(
            event_id=payload["event_id"],
            task_id=payload["task_id"],
            type=payload["type"],
            message=payload["message"],
            trace_id=payload["trace_id"],
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            metadata=payload.get("metadata", {}),
        )
