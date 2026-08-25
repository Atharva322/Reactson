"""Task persistence stores."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from reactson.core.events import TaskEvent
from reactson.core.session import TaskSession


class JsonTaskStore:
    def __init__(self, root: str | Path = "reactson_execution_logs") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: TaskSession) -> None:
        self._task_dir(session.task_id).mkdir(parents=True, exist_ok=True)
        self._session_path(session.task_id).write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")

    def load_session(self, task_id: str) -> TaskSession:
        return TaskSession.from_dict(json.loads(self._session_path(task_id).read_text(encoding="utf-8")))

    def append_event(self, event: TaskEvent) -> None:
        self._task_dir(event.task_id).mkdir(parents=True, exist_ok=True)
        events = self.load_events(event.task_id) if self._events_path(event.task_id).exists() else []
        events.append(event)
        self._events_path(event.task_id).write_text(
            json.dumps([item.to_dict() for item in events], indent=2),
            encoding="utf-8",
        )

    def load_events(self, task_id: str) -> list[TaskEvent]:
        path = self._events_path(task_id)
        if not path.exists():
            return []
        return [TaskEvent.from_dict(payload) for payload in json.loads(path.read_text(encoding="utf-8"))]

    def list_sessions(self) -> list[TaskSession]:
        sessions: list[TaskSession] = []
        for path in sorted(self.root.glob("*/session.json")):
            sessions.append(TaskSession.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        return sorted(sessions, key=lambda session: (session.created_at, session.task_id))

    def exists(self, task_id: str) -> bool:
        return self._session_path(task_id).exists()

    def readiness(self) -> bool:
        probe = self.root / f".readiness-{uuid4()}.tmp"
        probe.write_text("ok", encoding="utf-8")
        ok = probe.read_text(encoding="utf-8") == "ok"
        probe.unlink(missing_ok=True)
        return ok

    def _task_dir(self, task_id: str) -> Path:
        return self.root / task_id

    def _session_path(self, task_id: str) -> Path:
        return self._task_dir(task_id) / "session.json"

    def _events_path(self, task_id: str) -> Path:
        return self._task_dir(task_id) / "events.json"
