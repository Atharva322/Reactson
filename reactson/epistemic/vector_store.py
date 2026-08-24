"""Vector memory store contracts and in-memory implementation."""

from __future__ import annotations

import math

from reactson.epistemic.embeddings import HashEmbeddingService
from reactson.epistemic.models import ContextItem, ExecutionMemory


class InMemoryVectorStore:
    def __init__(self, embeddings: HashEmbeddingService | None = None) -> None:
        self.embeddings = embeddings or HashEmbeddingService()
        self._items: list[tuple[ExecutionMemory, tuple[float, ...]]] = []

    def add(self, memory: ExecutionMemory) -> None:
        self._items.append((memory, self.embeddings.embed(memory.text)))

    def search(self, query: str, task_id: str | None = None, limit: int = 5) -> list[ContextItem]:
        query_vector = self.embeddings.embed(query)
        matches: list[ContextItem] = []

        for memory, vector in self._items:
            if task_id is not None and memory.task_id != task_id:
                continue
            score = _cosine_similarity(query_vector, vector)
            matches.append(
                ContextItem(
                    text=memory.text,
                    source="vector",
                    score=score,
                    task_id=memory.task_id,
                    metadata={"memory_id": memory.memory_id, "tags": memory.tags},
                )
            )

        return sorted(matches, key=lambda item: item.score, reverse=True)[:limit]

    def recent(self, task_id: str, limit: int = 5) -> list[ContextItem]:
        memories = [memory for memory, _ in self._items if memory.task_id == task_id]
        memories.sort(key=lambda memory: memory.timestamp, reverse=True)
        return [
            ContextItem(
                text=memory.text,
                source="recent",
                score=1.0,
                task_id=memory.task_id,
                metadata={"memory_id": memory.memory_id, "tags": memory.tags},
            )
            for memory in memories[:limit]
        ]


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
