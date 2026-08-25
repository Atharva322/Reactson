"""Security regression checks."""

from __future__ import annotations

from dataclasses import dataclass

from reactson.engineering.test_runner import SafeTestRunner
from reactson.tools.models import ToolDefinition
from reactson.tools.sandbox import SandboxValidator


@dataclass(frozen=True)
class SecurityCheckResult:
    name: str
    passed: bool
    detail: str


def run_security_checks() -> tuple[SecurityCheckResult, ...]:
    sandbox = SandboxValidator()
    unsafe_tool = ToolDefinition(
        name="unsafe",
        description="Unsafe shell tool",
        capabilities=("shell",),
        schema={},
        handler=lambda: None,
        side_effects=("host_shell",),
    )
    sandbox_result = sandbox.validate(unsafe_tool)

    runner = SafeTestRunner(executor=lambda command, timeout: (0, "", ""))
    try:
        runner.run(("rm", "-rf", "."))
        command_rejected = False
    except ValueError:
        command_rejected = True

    return (
        SecurityCheckResult(
            name="sandbox_blocks_host_shell",
            passed=not sandbox_result.valid,
            detail="host_shell side effect rejected" if not sandbox_result.valid else "host_shell was allowed",
        ),
        SecurityCheckResult(
            name="safe_runner_rejects_unapproved_commands",
            passed=command_rejected,
            detail="unapproved command rejected" if command_rejected else "unapproved command allowed",
        ),
    )
