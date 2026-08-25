"""Task API route handlers independent of web framework plumbing."""

from __future__ import annotations

from typing import Any

from reactson.api.schemas import CreateTaskRequest, RunTaskRequest, event_payload, task_payload
from reactson.core.kernel import KernelRuntime


class TaskRoutes:
    def __init__(self, kernel: KernelRuntime) -> None:
        self.kernel = kernel

    def create_task(self, request: CreateTaskRequest) -> dict[str, Any]:
        return task_payload(self.kernel.create_task(request.objective, metadata=request.metadata))

    def list_tasks(self) -> list[dict[str, Any]]:
        return [task_payload(session) for session in self.kernel.list_tasks()]

    def get_task(self, task_id: str) -> dict[str, Any]:
        return task_payload(self.kernel.get_task(task_id))

    def run_task(self, task_id: str, request: RunTaskRequest | None = None) -> dict[str, Any]:
        active_request = request or RunTaskRequest()
        return task_payload(self.kernel.run_task(task_id, budget=active_request.budget))

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        return task_payload(self.kernel.cancel_task(task_id))

    def events(
        self,
        task_id: str,
        event_type: str | None = None,
        after_event_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return [
            event_payload(event)
            for event in self.kernel.events(task_id, event_type=event_type, after_event_id=after_event_id)
        ]

    def event_stream(self, task_id: str, after_event_id: str | None = None) -> str:
        return self.kernel.event_stream(task_id, after_event_id=after_event_id)

    def tree(self, task_id: str) -> dict[str, Any]:
        return self.kernel.tree(task_id)

    def health(self) -> dict[str, Any]:
        return self.kernel.health()

    def readiness(self) -> dict[str, Any]:
        return self.kernel.readiness()
