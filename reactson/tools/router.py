"""Tool capability router."""

from __future__ import annotations

from reactson.tools.models import CapabilityGap, ToolDefinition
from reactson.tools.registry import ToolRegistry


class ToolRouter:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def route(self, capability: str, arguments: dict | None = None) -> ToolDefinition | CapabilityGap:
        matches = self.registry.find_by_capability(capability)
        if not matches:
            return CapabilityGap(
                capability=capability,
                reason=f"No healthy registered tool supports capability '{capability}'.",
                requested_arguments=arguments or {},
            )
        return max(matches, key=lambda tool: (_capability_score(tool, capability), tool.name))


def _capability_score(tool: ToolDefinition, capability: str) -> int:
    requested = capability.lower()
    return max((len(existing) for existing in tool.capabilities if requested in existing.lower()), default=0)
