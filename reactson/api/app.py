"""Reactson API application factory and health contract."""

from __future__ import annotations

from typing import Any

from reactson import __version__
from reactson.api.routes import TaskRoutes
from reactson.api.schemas import CreateTaskRequest, RunTaskRequest
from reactson.config.settings import ReactsonSettings
from reactson.core.kernel import KernelRuntime


def health_payload(settings: ReactsonSettings | None = None) -> dict[str, Any]:
    active_settings = settings or ReactsonSettings.from_environment()
    return {
        "service": "reactson",
        "status": "ok",
        "version": __version__,
        "environment": active_settings.environment,
    }


def create_app(kernel: KernelRuntime | None = None) -> Any:
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError as exc:
        raise RuntimeError("Install Reactson with the 'api' extra to use create_app().") from exc

    app = FastAPI(title="Reactson API", version=__version__)
    routes = TaskRoutes(kernel or KernelRuntime())

    class CreateTaskBody(BaseModel):
        objective: str
        metadata: dict[str, Any] = {}

    class RunTaskBody(BaseModel):
        budget: int | None = None

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        return health_payload()

    @app.post("/v1/tasks")
    def create_task(body: CreateTaskBody) -> dict[str, Any]:
        return routes.create_task(CreateTaskRequest(objective=body.objective, metadata=body.metadata))

    @app.get("/v1/tasks/{task_id}")
    def get_task(task_id: str) -> dict[str, Any]:
        return routes.get_task(task_id)

    @app.post("/v1/tasks/{task_id}/run")
    def run_task(task_id: str, body: RunTaskBody | None = None) -> dict[str, Any]:
        return routes.run_task(task_id, RunTaskRequest(budget=body.budget if body else None))

    @app.post("/v1/tasks/{task_id}/cancel")
    def cancel_task(task_id: str) -> dict[str, Any]:
        return routes.cancel_task(task_id)

    @app.get("/v1/tasks/{task_id}/events")
    def task_events(task_id: str) -> list[dict[str, Any]]:
        return routes.events(task_id)

    @app.get("/v1/tasks/{task_id}/tree")
    def task_tree(task_id: str) -> dict[str, Any]:
        return routes.tree(task_id)

    @app.get("/v1/tools")
    def tools() -> list[dict[str, Any]]:
        return []

    return app
