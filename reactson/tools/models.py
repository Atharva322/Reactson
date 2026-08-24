"""Tool model types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    capabilities: tuple[str, ...]
    schema: dict[str, Any]
    handler: ToolHandler
    allowed_action_types: tuple[str, ...] = ("tool",)
    side_effects: tuple[str, ...] = ()
    healthy: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityGap:
    capability: str
    reason: str
    requested_arguments: dict[str, Any] = field(default_factory=dict)
