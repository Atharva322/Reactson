"""Reactson API application factory and health contract."""

from __future__ import annotations

from typing import Any

from reactson import __version__
from reactson.config.settings import ReactsonSettings


def health_payload(settings: ReactsonSettings | None = None) -> dict[str, Any]:
    active_settings = settings or ReactsonSettings.from_environment()
    return {
        "service": "reactson",
        "status": "ok",
        "version": __version__,
        "environment": active_settings.environment,
    }


def create_app() -> Any:
    try:
        from fastapi import FastAPI
    except ImportError as exc:
        raise RuntimeError("Install Reactson with the 'api' extra to use create_app().") from exc

    app = FastAPI(title="Reactson API", version=__version__)

    @app.get("/v1/health")
    def health() -> dict[str, Any]:
        return health_payload()

    return app
