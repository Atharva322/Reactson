"""Executor boundary for tool side effects."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from reactson.execution.models import Action, ExecutionResult
from reactson.tools.registry import ToolRegistry


class Executor:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def execute(self, action: Action) -> ExecutionResult:
        started = perf_counter()
        tool = self.registry.get(action.tool_name)
        if tool is None:
            return _result(
                started,
                success=False,
                error=f"Tool '{action.tool_name}' is not registered.",
                metadata={"tool_name": action.tool_name, "action_type": action.type},
            )

        allowed, reason = self.registry.is_allowed(action.tool_name, action.type)
        if not allowed:
            return _result(
                started,
                success=False,
                error=reason,
                metadata={"tool_name": action.tool_name, "action_type": action.type},
            )

        try:
            output = tool.handler(**action.arguments)
        except Exception as exc:  # pragma: no cover - exact exception type belongs to tool implementation
            return _result(
                started,
                success=False,
                error=str(exc),
                metadata={"tool_name": action.tool_name, "action_type": action.type},
            )

        return _result(
            started,
            success=True,
            output=output,
            side_effects=tool.side_effects,
            metadata={"tool_name": action.tool_name, "action_type": action.type},
        )


def _result(
    started: float,
    *,
    success: bool,
    output: Any = None,
    error: str | None = None,
    side_effects: tuple[str, ...] = (),
    metadata: dict[str, Any] | None = None,
) -> ExecutionResult:
    return ExecutionResult(
        success=success,
        output=output,
        error=error,
        latency_ms=(perf_counter() - started) * 1000,
        side_effects=side_effects,
        metadata=metadata or {},
    )
