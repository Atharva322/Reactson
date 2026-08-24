"""High-level epistemic memory facade."""

from __future__ import annotations

from reactson.epistemic.context_router import ContextRouter
from reactson.epistemic.graph_store import InMemoryGraphStore
from reactson.epistemic.ingestion import MemoryIngestionPipeline
from reactson.epistemic.models import ContextItem, ExecutionMemory, GraphTriple
from reactson.epistemic.vector_store import InMemoryVectorStore


class EpistemicEngine:
    def __init__(
        self,
        graph_store: InMemoryGraphStore | None = None,
        vector_store: InMemoryVectorStore | None = None,
        context_router: ContextRouter | None = None,
    ) -> None:
        self.graph_store = graph_store or InMemoryGraphStore()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.context_router = context_router or ContextRouter()
        self.ingestion = MemoryIngestionPipeline(self.graph_store, self.vector_store)

    def remember_episode(self, memory: ExecutionMemory) -> ExecutionMemory:
        return self.ingestion.ingest_episode(memory)

    def remember_fact(self, triple: GraphTriple) -> GraphTriple:
        return self.ingestion.ingest_fact(triple)

    def retrieve_context(
        self,
        *,
        task_id: str,
        query: str,
        entities: tuple[str, ...] = (),
        recent_limit: int = 5,
        semantic_limit: int = 5,
        graph_depth: int = 1,
    ) -> list[ContextItem]:
        graph_items: list[ContextItem] = []
        for entity in entities:
            graph_items.extend(self.graph_store.neighbors(task_id, entity, depth=graph_depth))

        return self.context_router.route(
            [
                self.vector_store.recent(task_id, limit=recent_limit),
                self.vector_store.search(query, task_id=task_id, limit=semantic_limit),
                graph_items,
            ]
        )
