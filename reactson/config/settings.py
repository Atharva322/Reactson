"""Reactson configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ReactsonSettings:
    environment: str = "development"
    execution_log_dir: str = "reactson_execution_logs"
    tool_schema_dir: str = "reactson_tool_schemas"
    kernel_name: str = "reactson-kernel"

    @classmethod
    def from_environment(cls) -> "ReactsonSettings":
        return cls(environment=os.getenv("REACTSON_ENV", cls.environment))
