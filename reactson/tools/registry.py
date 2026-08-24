"""In-memory tool registry."""

from __future__ import annotations

from reactson.tools.models import ToolDefinition


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list(self) -> tuple[ToolDefinition, ...]:
        return tuple(sorted(self._tools.values(), key=lambda tool: tool.name))

    def find_by_capability(self, capability: str) -> list[ToolDefinition]:
        requested = capability.lower()
        return [
            tool
            for tool in self._tools.values()
            if tool.healthy and any(requested in existing.lower() for existing in tool.capabilities)
        ]

    def is_allowed(self, tool_name: str, action_type: str) -> tuple[bool, str | None]:
        tool = self.get(tool_name)
        if tool is None:
            return False, f"Tool '{tool_name}' is not registered."
        if not tool.healthy:
            return False, f"Tool '{tool_name}' is unhealthy."
        if action_type not in tool.allowed_action_types:
            return False, f"Tool '{tool_name}' does not allow action type '{action_type}'."
        return True, None
