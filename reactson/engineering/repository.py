"""Safe repository inspection tools."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from reactson.engineering.models import Evidence, relative_path


class RepositoryTools:
    def __init__(
        self,
        root: str | Path,
        ignored_dirs: tuple[str, ...] = (".git", "__pycache__", ".pytest_cache", ".test-artifacts"),
    ) -> None:
        self.root = Path(root).resolve()
        self.ignored_dirs = ignored_dirs

    def list_files(self, pattern: str = "*") -> tuple[str, ...]:
        files: list[str] = []
        for path in self._walk_files():
            if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(relative_path(self.root, path), pattern):
                files.append(relative_path(self.root, path))
        return tuple(sorted(files))

    def search(self, pattern: str, file_glob: str = "*") -> tuple[Evidence, ...]:
        matches: list[Evidence] = []
        lowered = pattern.lower()
        for path in self._walk_files():
            rel = relative_path(self.root, path)
            if not fnmatch.fnmatch(path.name, file_glob) and not fnmatch.fnmatch(rel, file_glob):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for index, line in enumerate(lines, start=1):
                if lowered in line.lower():
                    matches.append(Evidence(source="code_search", detail=line.strip(), path=rel, line=index))
        return tuple(matches)

    def collect_failure_files(self) -> tuple[Evidence, ...]:
        evidence: list[Evidence] = []
        for pattern in ("test_*.py", "*_test.py", "pyproject.toml", "README.md"):
            for file_path in self.list_files(pattern):
                evidence.append(Evidence(source="repository_file", detail=f"Found {pattern}", path=file_path))
        return tuple(evidence)

    def _walk_files(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                continue
            relative_parts = path.relative_to(self.root).parts
            if any(part in self.ignored_dirs for part in relative_parts):
                continue
            yield path
