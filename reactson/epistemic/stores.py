"""Memory store protocols."""

from __future__ import annotations

from typing import Protocol

from reactson.epistemic.models import ContextItem, ExecutionMemory, GraphTriple


class GraphStore(Protocol):
    def add(self, triple: GraphTriple) -> None:
        ...

    def neighbors(self, task_id: str, entity: str, depth: int = 1, limit: int = 10) -> list[ContextItem]:
        ...

    def validate_schema(self) -> bool:
        ...


class VectorStore(Protocol):
    def add(self, memory: ExecutionMemory) -> None:
        ...

    def search(self, query: str, task_id: str | None = None, limit: int = 5) -> list[ContextItem]:
        ...

    def recent(self, task_id: str, limit: int = 5) -> list[ContextItem]:
        ...

    def validate_collection(self) -> bool:
        ...
