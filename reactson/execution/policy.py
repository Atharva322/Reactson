"""Execution retry policy."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.execution.models import Action, ExecutionResult


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    retryable_errors: tuple[str, ...] = ("timeout", "transient", "temporary")

    def should_retry(self, action: Action, result: ExecutionResult, attempt: int) -> bool:
        if result.success or attempt >= self.max_attempts:
            return False
        error = (result.error or "").lower()
        return any(marker in error for marker in self.retryable_errors)
