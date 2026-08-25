"""Executor boundary for tool side effects."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from reactson.execution.models import Action, ExecutionResult
from reactson.execution.policy import RetryPolicy
from reactson.epistemic.engine import EpistemicEngine
from reactson.epistemic.models import ExecutionMemory
from reactson.tools.registry import ToolRegistry


class Executor:
    def __init__(
        self,
        registry: ToolRegistry,
        retry_policy: RetryPolicy | None = None,
        memory: EpistemicEngine | None = None,
        task_id: str | None = None,
    ) -> None:
        self.registry = registry
        self.retry_policy = retry_policy or RetryPolicy()
        self.memory = memory
        self.task_id = task_id

    def execute(self, action: Action) -> ExecutionResult:
        last_result: ExecutionResult | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            result = self._execute_once(action, attempt)
            last_result = result
            if not self.retry_policy.should_retry(action, result, attempt):
                self._remember(action, result)
                return result

        assert last_result is not None
        self._remember(action, last_result)
        return last_result

    def _execute_once(self, action: Action, attempt: int) -> ExecutionResult:
        started = perf_counter()
        tool = self.registry.get(action.tool_name)
        if tool is None:
            return _result(
                started,
                success=False,
                error=f"Tool '{action.tool_name}' is not registered.",
                metadata={"tool_name": action.tool_name, "action_type": action.type, "attempt": attempt},
            )

        allowed, reason = self.registry.is_allowed(action.tool_name, action.type)
        if not allowed:
            return _result(
                started,
                success=False,
                error=reason,
                metadata={"tool_name": action.tool_name, "action_type": action.type, "attempt": attempt},
            )

        try:
            output = tool.handler(**action.arguments)
        except Exception as exc:  # pragma: no cover - exact exception type belongs to tool implementation
            return _result(
                started,
                success=False,
                error=str(exc),
                metadata={"tool_name": action.tool_name, "action_type": action.type, "attempt": attempt},
            )

        return _result(
            started,
            success=True,
            output=output,
            side_effects=tool.side_effects,
            metadata={"tool_name": action.tool_name, "action_type": action.type, "attempt": attempt},
        )

    def _remember(self, action: Action, result: ExecutionResult) -> None:
        if self.memory is None or self.task_id is None:
            return
        self.memory.remember_episode(
            ExecutionMemory(
                task_id=self.task_id,
                text=f"Tool {action.tool_name} {'succeeded' if result.success else 'failed'}: {result.output or result.error}",
                action=action.tool_name,
                result=str(result.output if result.success else result.error),
                reward=1.0 if result.success else -1.0,
                tags=("tool_result", action.type),
                metadata={"tool_name": action.tool_name, "success": result.success},
            )
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
