"""Documentation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentationCheckResult:
    path: str
    passed: bool
    missing_terms: tuple[str, ...] = ()


def verify_documentation(root: str | Path = ".") -> tuple[DocumentationCheckResult, ...]:
    base = Path(root)
    checks = {
        "README.md": ("Reactson", "Quick Start", "CLI", "API"),
        "PHASES.md": ("Phase 0", "Phase 6", "Status"),
        "UPSTREAM.md": ("Nexus", "Apache-2.0"),
    }
    results: list[DocumentationCheckResult] = []
    for path, required_terms in checks.items():
        full_path = base / path
        text = full_path.read_text(encoding="utf-8") if full_path.exists() else ""
        missing = tuple(term for term in required_terms if term not in text)
        results.append(DocumentationCheckResult(path=path, passed=not missing, missing_terms=missing))
    return tuple(results)
