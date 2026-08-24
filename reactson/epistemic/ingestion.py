"""Memory ingestion pipeline."""

from __future__ import annotations

from reactson.epistemic.graph_store import InMemoryGraphStore
from reactson.epistemic.models import ExecutionMemory, GraphTriple
from reactson.epistemic.stores import GraphStore, VectorStore
from reactson.epistemic.vector_store import InMemoryVectorStore


class MemoryIngestionPipeline:
    def __init__(self, graph_store: GraphStore, vector_store: VectorStore) -> None:
        self.graph_store = graph_store
        self.vector_store = vector_store

    def ingest_episode(self, memory: ExecutionMemory) -> ExecutionMemory:
        self.vector_store.add(memory)
        return memory

    def ingest_fact(self, triple: GraphTriple) -> GraphTriple:
        self.graph_store.add(triple)
        return triple
