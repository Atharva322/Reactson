from __future__ import annotations

import pytest

from reactson.execution import Action, ExecutionCritic, Executor
from reactson.tools import CapabilityGap, ToolDefinition, ToolRegistry, ToolRouter


def test_tool_router_selects_registered_capability() -> None:
    registry = ToolRegistry()
    registry.register(_echo_tool())
    router = ToolRouter(registry)

    routed = router.route("echo")

    assert isinstance(routed, ToolDefinition)
    assert routed.name == "echo"


def test_tool_router_returns_capability_gap_when_missing() -> None:
    router = ToolRouter(ToolRegistry())

    routed = router.route("summarize", {"text": "hello"})

    assert isinstance(routed, CapabilityGap)
    assert routed.capability == "summarize"
    assert routed.requested_arguments == {"text": "hello"}


def test_executor_runs_registered_tool_and_reports_metadata() -> None:
    registry = ToolRegistry()
    registry.register(_echo_tool())
    executor = Executor(registry)

    result = executor.execute(
        Action(
            type="tool",
            tool_name="echo",
            arguments={"text": "hello"},
            expected_outcome="returns text",
        )
    )

    assert result.success is True
    assert result.output == "hello"
    assert result.metadata == {"tool_name": "echo", "action_type": "tool"}


def test_executor_rejects_unregistered_tool() -> None:
    result = Executor(ToolRegistry()).execute(Action(type="tool", tool_name="missing"))

    assert result.success is False
    assert "not registered" in result.error


def test_executor_enforces_action_type_permissions() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="read_only",
            description="Read-only demo tool",
            capabilities=("read",),
            schema={},
            handler=lambda: "ok",
            allowed_action_types=("read",),
        )
    )

    result = Executor(registry).execute(Action(type="write", tool_name="read_only"))

    assert result.success is False
    assert "does not allow" in result.error


def test_executor_captures_tool_errors() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="explode",
            description="Tool that raises",
            capabilities=("explode",),
            schema={},
            handler=_explode,
        )
    )

    result = Executor(registry).execute(Action(type="tool", tool_name="explode"))

    assert result.success is False
    assert result.error == "boom"


def test_execution_critic_scores_success_and_side_effect_costs() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="write_demo",
            description="Write demo",
            capabilities=("write",),
            schema={},
            handler=lambda: "written",
            side_effects=("filesystem",),
        )
    )
    action = Action(type="tool", tool_name="write_demo", expected_outcome="writes")
    result = Executor(registry).execute(action)

    critique = ExecutionCritic(side_effect_penalty=0.2).evaluate(action, result)

    assert critique.diagnosis == "tool_success"
    assert critique.reward < 1.0
    assert critique.signals["side_effect_penalty"] == pytest.approx(0.2)


def test_registry_rejects_duplicate_tool_names() -> None:
    registry = ToolRegistry()
    registry.register(_echo_tool())

    with pytest.raises(ValueError):
        registry.register(_echo_tool())


def _echo_tool() -> ToolDefinition:
    return ToolDefinition(
        name="echo",
        description="Echo text",
        capabilities=("echo", "text echo"),
        schema={"type": "object", "properties": {"text": {"type": "string"}}},
        handler=lambda text: text,
    )


def _explode():
    raise RuntimeError("boom")
