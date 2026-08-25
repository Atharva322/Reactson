"""Deterministic safe demo tool synthesizer."""

from __future__ import annotations

import re

from reactson.tools.models import CapabilityGap, ToolDefinition
from reactson.tools.sandbox import SandboxValidator


class ToolSynthesizer:
    def __init__(self, sandbox: SandboxValidator | None = None) -> None:
        self.sandbox = sandbox or SandboxValidator()

    def synthesize(self, gap: CapabilityGap) -> ToolDefinition:
        capability = gap.capability.strip().lower()
        if capability not in {"echo", "uppercase", "word_count"}:
            raise ValueError(f"Capability '{gap.capability}' is not approved for deterministic synthesis.")

        tool = _safe_demo_tool(capability)
        validation = self.sandbox.validate(tool)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
        return tool


def _safe_demo_tool(capability: str) -> ToolDefinition:
    name = f"synthetic_{capability}"
    schema = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}
    if capability == "echo":
        return ToolDefinition(
            name=name,
            description="Synthetic echo demo tool",
            capabilities=("echo",),
            schema=schema,
            handler=lambda text: text,
            metadata={"synthetic": True},
        )
    if capability == "uppercase":
        return ToolDefinition(
            name=name,
            description="Synthetic uppercase demo tool",
            capabilities=("uppercase",),
            schema=schema,
            handler=lambda text: text.upper(),
            metadata={"synthetic": True},
        )
    return ToolDefinition(
        name=name,
        description="Synthetic word-count demo tool",
        capabilities=("word_count",),
        schema=schema,
        handler=lambda text: len(re.findall(r"[A-Za-z0-9_]+", text)),
        metadata={"synthetic": True},
    )
