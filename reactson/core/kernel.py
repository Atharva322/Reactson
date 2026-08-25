"""Reactson kernel runtime."""

from __future__ import annotations

from reactson.core.events import TaskEvent
from reactson.core.persistence import JsonTaskStore
from reactson.core.session import TaskSession, TaskStatus


class KernelRuntime:
    def __init__(self, store: JsonTaskStore | None = None) -> None:
        self.store = store or JsonTaskStore()

    def create_task(self, objective: str, metadata: dict | None = None) -> TaskSession:
        session = TaskSession(objective=objective, metadata=metadata or {})
        self.store.save_session(session)
        self._record(session, "task.created", "Task created")
        return session

    def get_task(self, task_id: str) -> TaskSession:
        return self.store.load_session(task_id)

    def run_task(self, task_id: str, budget: int | None = None) -> TaskSession:
        session = self.store.load_session(task_id)
        if session.status in {TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.HALTED}:
            return session

        for status, message in (
            (TaskStatus.PLANNING, "Planning started"),
            (TaskStatus.EXECUTING, "Execution started"),
            (TaskStatus.EVALUATING, "Evaluation started"),
        ):
            session.transition(status)
            self.store.save_session(session)
            self._record(session, f"task.{status.value.lower()}", message)

        session.result = f"Completed objective: {session.objective}"
        session.metadata["budget"] = budget
        session.transition(TaskStatus.COMPLETED)
        self.store.save_session(session)
        self._record(session, "task.completed", "Task completed")
        return session

    def cancel_task(self, task_id: str) -> TaskSession:
        session = self.store.load_session(task_id)
        if session.status != TaskStatus.COMPLETED:
            session.transition(TaskStatus.CANCELLED)
            self.store.save_session(session)
            self._record(session, "task.cancelled", "Task cancelled")
        return session

    def events(self, task_id: str) -> list[TaskEvent]:
        return self.store.load_events(task_id)

    def tree(self, task_id: str) -> dict:
        session = self.store.load_session(task_id)
        return {
            "task_id": task_id,
            "status": session.status.value,
            "tree": session.metadata.get("tree", {}),
        }

    def health(self) -> dict[str, str]:
        return {"kernel": "ok", "persistence": "ok"}

    def _record(self, session: TaskSession, event_type: str, message: str) -> None:
        self.store.append_event(
            TaskEvent(
                task_id=session.task_id,
                type=event_type,
                message=message,
                trace_id=session.trace_id,
            )
        )
