"""Safe test-runner abstraction for repository diagnosis."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
import subprocess

from reactson.engineering.models import Evidence


CommandExecutor = Callable[[tuple[str, ...], int], tuple[int, str, str]]


@dataclass(frozen=True)
class TestRunResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0

    def evidence(self) -> tuple[Evidence, ...]:
        return parse_test_output(self.stdout, self.stderr)


class SafeTestRunner:
    allowed_commands = frozenset({"pytest", "python"})

    def __init__(self, executor: CommandExecutor | None = None, timeout_seconds: int = 30) -> None:
        self.executor = executor or _subprocess_executor
        self.timeout_seconds = timeout_seconds

    def run(self, command: tuple[str, ...] = ("pytest", "-q")) -> TestRunResult:
        if not command:
            raise ValueError("command must not be empty")
        if command[0] not in self.allowed_commands:
            raise ValueError(f"Command '{command[0]}' is not allowed.")
        exit_code, stdout, stderr = self.executor(command, self.timeout_seconds)
        return TestRunResult(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)


def parse_test_output(stdout: str, stderr: str = "") -> tuple[Evidence, ...]:
    combined = "\n".join(part for part in (stdout, stderr) if part)
    evidence: list[Evidence] = []
    for line in combined.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        file_match = re.search(r"(?P<path>[\w./\\-]*test[\w./\\-]*\.py):(?P<line>\d+)", stripped)
        if file_match:
            evidence.append(
                Evidence(
                    source="test_output",
                    detail=stripped,
                    path=file_match.group("path").replace("\\", "/"),
                    line=int(file_match.group("line")),
                )
            )
        elif any(marker in stripped for marker in ("FAILED", "ERROR", "ImportError", "AssertionError")):
            evidence.append(Evidence(source="test_output", detail=stripped))
    return tuple(evidence)


def _subprocess_executor(command: tuple[str, ...], timeout_seconds: int) -> tuple[int, str, str]:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        shell=False,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr
