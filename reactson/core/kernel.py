"""Reactson kernel runtime."""

from __future__ import annotations

from reactson.core.events import TaskEvent
from reactson.core.persistence import JsonTaskStore
from reactson.core.session import TaskSession, TaskStatus
from reactson.observability.metrics import MetricsRegistry
from reactson.observability.tracing import Tracer


class KernelRuntime:
    def __init__(
        self,
        store: JsonTaskStore | None = None,
        metrics: MetricsRegistry | None = None,
        tracer: Tracer | None = None,
    ) -> None:
        self.store = store or JsonTaskStore()
        self.metrics = metrics or MetricsRegistry()
        self.tracer = tracer or Tracer()

    def create_task(self, objective: str, metadata: dict | None = None) -> TaskSession:
        session = TaskSession(objective=objective, metadata=metadata or {})
        self.store.save_session(session)
        self.metrics.increment("tasks_created")
        self._record(session, "task.created", "Task created")
        return session

    def get_task(self, task_id: str) -> TaskSession:
        return self.store.load_session(task_id)

    def run_task(self, task_id: str, budget: int | None = None) -> TaskSession:
        session = self.store.load_session(task_id)
        if session.status in {TaskStatus.CANCELLED, TaskStatus.COMPLETED, TaskStatus.HALTED}:
            return session

        if budget is not None and budget <= 0:
            session.metadata["budget"] = budget
            session.transition(TaskStatus.HALTED)
            self.store.save_session(session)
            self.metrics.increment("tasks_halted")
            self._record(session, "task.halted", "Task halted by budget")
            return session

        for status, message in (
            (TaskStatus.PLANNING, "Planning started"),
            (TaskStatus.EXECUTING, "Execution started"),
            (TaskStatus.EVALUATING, "Evaluation started"),
        ):
            session.transition(status)
            self.store.save_session(session)
            self.metrics.increment(f"task_status_{status.value.lower()}")
            self._record(session, f"task.{status.value.lower()}", message)

        session.result = f"Completed objective: {session.objective}"
        session.metadata["budget"] = budget
        session.transition(TaskStatus.COMPLETED)
        self.store.save_session(session)
        self.metrics.increment("tasks_completed")
        self._record(session, "task.completed", "Task completed")
        return session

    def cancel_task(self, task_id: str) -> TaskSession:
        session = self.store.load_session(task_id)
        if session.status != TaskStatus.COMPLETED:
            session.transition(TaskStatus.CANCELLED)
            self.store.save_session(session)
            self.metrics.increment("tasks_cancelled")
            self._record(session, "task.cancelled", "Task cancelled")
        return session

    def events(self, task_id: str, event_type: str | None = None) -> list[TaskEvent]:
        events = self.store.load_events(task_id)
        if event_type is None:
            return events
        return [event for event in events if event.type == event_type]

    def tree(self, task_id: str) -> dict:
        session = self.store.load_session(task_id)
        return {
            "task_id": task_id,
            "status": session.status.value,
            "tree": session.metadata.get("tree", {}),
        }

    def health(self) -> dict:
        return {"kernel": "ok", "persistence": "ok", "metrics": self.metrics.snapshot()}

    def readiness(self) -> dict[str, bool]:
        return {"ready": True, "persistence": True}

    def _record(self, session: TaskSession, event_type: str, message: str) -> None:
        span = self.tracer.start_span(event_type, session.trace_id, attributes={"task_id": session.task_id})
        self.store.append_event(
            TaskEvent(
                task_id=session.task_id,
                type=event_type,
                message=message,
                trace_id=session.trace_id,
                metadata={"span": span.to_dict()},
            )
        )
