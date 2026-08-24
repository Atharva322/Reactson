"""Vector memory store implementations."""

from __future__ import annotations

import math
from typing import Any

from reactson.epistemic.embeddings import HashEmbeddingService
from reactson.epistemic.errors import MemoryStoreConfigurationError
from reactson.epistemic.models import ContextItem, ExecutionMemory


class InMemoryVectorStore:
    def __init__(self, embeddings: HashEmbeddingService | None = None) -> None:
        self.embeddings = embeddings or HashEmbeddingService()
        self._items: list[tuple[ExecutionMemory, tuple[float, ...]]] = []

    def add(self, memory: ExecutionMemory) -> None:
        self._items.append((memory, self.embeddings.embed(memory.text)))

    def validate_collection(self) -> bool:
        return True

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


class QdrantVectorStore:
    """Qdrant vector store adapter with injectable client for tests."""

    def __init__(
        self,
        client: Any,
        collection_name: str,
        embeddings: HashEmbeddingService | None = None,
    ) -> None:
        self.client = client
        self.collection_name = collection_name
        self.embeddings = embeddings or HashEmbeddingService()

    @classmethod
    def from_connection(
        cls,
        *,
        url: str,
        collection_name: str,
        api_key: str | None = None,
        embeddings: HashEmbeddingService | None = None,
    ) -> "QdrantVectorStore":
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise MemoryStoreConfigurationError(
                "Install Reactson with the 'memory' extra to use QdrantVectorStore."
            ) from exc

        return cls(QdrantClient(url=url, api_key=api_key), collection_name, embeddings=embeddings)

    def add(self, memory: ExecutionMemory) -> None:
        point = {
            "id": memory.memory_id,
            "vector": list(self.embeddings.embed(memory.text)),
            "payload": {
                "task_id": memory.task_id,
                "text": memory.text,
                "action": memory.action,
                "result": memory.result,
                "reward": memory.reward,
                "tags": list(memory.tags),
                "timestamp": memory.timestamp.isoformat(),
                "metadata": memory.metadata,
            },
        }
        self.client.upsert(collection_name=self.collection_name, points=[point])

    def search(self, query: str, task_id: str | None = None, limit: int = 5) -> list[ContextItem]:
        query_filter = None
        if task_id is not None:
            query_filter = {"must": [{"key": "task_id", "match": {"value": task_id}}]}

        records = self.client.search(
            collection_name=self.collection_name,
            query_vector=list(self.embeddings.embed(query)),
            query_filter=query_filter,
            limit=limit,
        )
        return [_point_to_context_item(record, source="vector") for record in records]

    def recent(self, task_id: str, limit: int = 5) -> list[ContextItem]:
        records, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter={"must": [{"key": "task_id", "match": {"value": task_id}}]},
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        items = [_point_to_context_item(record, source="recent", score=1.0) for record in records]
        return sorted(items, key=lambda item: item.metadata.get("timestamp", ""), reverse=True)

    def validate_collection(self) -> bool:
        self.client.get_collection(collection_name=self.collection_name)
        return True


def _point_to_context_item(record: Any, source: str, score: float | None = None) -> ContextItem:
    payload = _get_value(record, "payload", {}) or {}
    return ContextItem(
        text=payload["text"],
        source=source,
        score=float(score if score is not None else _get_value(record, "score", 0.0)),
        task_id=payload["task_id"],
        metadata={
            "memory_id": str(_get_value(record, "id", "")),
            "tags": tuple(payload.get("tags", ())),
            "timestamp": payload.get("timestamp", ""),
            "metadata": payload.get("metadata", {}),
        },
    )


def _get_value(record: Any, key: str, default: Any = None) -> Any:
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)
