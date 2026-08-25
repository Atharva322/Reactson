from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from reactson.api.routes import TaskRoutes
from reactson.api.schemas import CreateTaskRequest, RunTaskRequest
from reactson.core.kernel import KernelRuntime
from reactson.core.persistence import JsonTaskStore
from reactson.core.session import TaskStatus


def test_kernel_task_lifecycle_persists_events() -> None:
    store = JsonTaskStore(_workspace_tmp())
    kernel = KernelRuntime(store)

    created = kernel.create_task("diagnose failing tests", metadata={"suite": "unit"})
    completed = kernel.run_task(created.task_id, budget=3)
    events = kernel.events(created.task_id)

    assert created.status == TaskStatus.CREATED
    assert completed.status == TaskStatus.COMPLETED
    assert completed.result == "Completed objective: diagnose failing tests"
    assert [event.type for event in events] == [
        "task.created",
        "task.planning",
        "task.executing",
        "task.evaluating",
        "task.completed",
    ]
    assert {event.trace_id for event in events} == {created.trace_id}


def test_kernel_can_resume_task_from_json_store() -> None:
    root = _workspace_tmp()
    first_kernel = KernelRuntime(JsonTaskStore(root))
    created = first_kernel.create_task("persist me")

    second_kernel = KernelRuntime(JsonTaskStore(root))
    loaded = second_kernel.get_task(created.task_id)

    assert loaded.task_id == created.task_id
    assert loaded.objective == "persist me"
    assert loaded.status == TaskStatus.CREATED


def test_kernel_cancel_halts_unfinished_task() -> None:
    kernel = KernelRuntime(JsonTaskStore(_workspace_tmp()))
    created = kernel.create_task("cancel me")

    cancelled = kernel.cancel_task(created.task_id)

    assert cancelled.status == TaskStatus.CANCELLED
    assert kernel.events(created.task_id)[-1].type == "task.cancelled"


def test_task_routes_wrap_kernel_contracts() -> None:
    routes = TaskRoutes(KernelRuntime(JsonTaskStore(_workspace_tmp())))

    created = routes.create_task(CreateTaskRequest(objective="route objective"))
    completed = routes.run_task(created["task_id"], RunTaskRequest(budget=1))
    fetched = routes.get_task(created["task_id"])
    events = routes.events(created["task_id"])
    tree = routes.tree(created["task_id"])

    assert completed["status"] == "COMPLETED"
    assert fetched["objective"] == "route objective"
    assert events[0]["type"] == "task.created"
    assert tree["task_id"] == created["task_id"]


def test_kernel_records_metrics_and_trace_spans() -> None:
    kernel = KernelRuntime(JsonTaskStore(_workspace_tmp()))
    created = kernel.create_task("observe me")
    kernel.run_task(created.task_id)

    health = kernel.health()
    events = kernel.events(created.task_id)

    assert health["metrics"]["counters"]["tasks_created"] == 1.0
    assert health["metrics"]["counters"]["tasks_completed"] == 1.0
    assert events[0].metadata["span"]["trace_id"] == created.trace_id
    assert events[0].metadata["span"]["name"] == "task.created"


def test_kernel_halts_when_budget_is_exhausted() -> None:
    kernel = KernelRuntime(JsonTaskStore(_workspace_tmp()))
    created = kernel.create_task("budget stop")

    halted = kernel.run_task(created.task_id, budget=0)

    assert halted.status == TaskStatus.HALTED
    assert kernel.events(created.task_id)[-1].type == "task.halted"
    assert kernel.health()["metrics"]["counters"]["tasks_halted"] == 1.0


def test_events_can_be_filtered_by_type() -> None:
    kernel = KernelRuntime(JsonTaskStore(_workspace_tmp()))
    created = kernel.create_task("filter events")
    kernel.run_task(created.task_id)

    completed_events = kernel.events(created.task_id, event_type="task.completed")

    assert [event.type for event in completed_events] == ["task.completed"]


def test_routes_expose_health_readiness_and_filtered_events() -> None:
    routes = TaskRoutes(KernelRuntime(JsonTaskStore(_workspace_tmp())))
    created = routes.create_task(CreateTaskRequest(objective="route health"))
    routes.run_task(created["task_id"])

    assert routes.health()["kernel"] == "ok"
    assert routes.readiness() == {"ready": True, "persistence": True}
    assert routes.events(created["task_id"], event_type="task.completed")[0]["type"] == "task.completed"


def _workspace_tmp() -> Path:
    root = Path(".test-artifacts") / str(uuid4())
    root.mkdir(parents=True, exist_ok=True)
    return root
