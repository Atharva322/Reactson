"""Sandbox validation for generated or registered tools."""

from __future__ import annotations

from dataclasses import dataclass, field

from reactson.tools.models import ToolDefinition


@dataclass(frozen=True)
class SandboxValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


class SandboxValidator:
    blocked_side_effects = frozenset({"host_shell", "unrestricted_filesystem", "network"})

    def validate(self, tool: ToolDefinition) -> SandboxValidationResult:
        errors: list[str] = []
        if not tool.name:
            errors.append("tool name is required")
        if not tool.capabilities:
            errors.append("at least one capability is required")
        blocked = sorted(set(tool.side_effects).intersection(self.blocked_side_effects))
        if blocked:
            errors.append(f"blocked side effects: {', '.join(blocked)}")
        if not isinstance(tool.schema, dict):
            errors.append("schema must be a dictionary")

        return SandboxValidationResult(
            valid=not errors,
            errors=tuple(errors),
            metadata={"validator": "deterministic"},
        )
