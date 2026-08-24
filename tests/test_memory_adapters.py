from __future__ import annotations

from reactson.epistemic import EpistemicEngine, ExecutionMemory, GraphTriple
from reactson.epistemic.graph_store import Neo4jGraphStore
from reactson.epistemic.vector_store import QdrantVectorStore


def test_engine_validates_memory_backends() -> None:
    engine = EpistemicEngine()

    assert engine.validate_backends() == {"graph": True, "vector": True}


def test_neo4j_adapter_writes_triples_and_reads_neighbors() -> None:
    driver = FakeNeo4jDriver(
        records=[
            {
                "source": "Task",
                "relation": "HAS_HYPOTHESIS",
                "target": "Hypothesis",
                "evidence": "failure signature matched",
                "metadata": {"confidence": 0.8},
            }
        ]
    )
    store = Neo4jGraphStore(driver)

    store.add(GraphTriple(task_id="task-a", source="Task", relation="HAS_HYPOTHESIS", target="Hypothesis"))
    neighbors = store.neighbors("task-a", "Task")

    assert driver.calls[0]["parameters"]["source"] == "Task"
    assert neighbors[0].text == "Task -[HAS_HYPOTHESIS]-> Hypothesis. Evidence: failure signature matched"
    assert neighbors[0].metadata == {"confidence": 0.8}


def test_qdrant_adapter_upserts_and_searches_task_filtered_points() -> None:
    client = FakeQdrantClient()
    store = QdrantVectorStore(client, "reactson_execution_memory")
    memory = ExecutionMemory(task_id="task-a", text="pytest failure caused by missing import", tags=("failure",))

    store.add(memory)
    results = store.search("missing import", task_id="task-a", limit=1)

    assert client.upserts[0]["collection_name"] == "reactson_execution_memory"
    assert client.searches[0]["query_filter"] == {
        "must": [{"key": "task_id", "match": {"value": "task-a"}}]
    }
    assert results[0].text == memory.text
    assert results[0].task_id == "task-a"


class FakeNeo4jDriver:
    def __init__(self, records):
        self.records = records
        self.calls = []

    def execute_query(self, query, parameters_, database_=None):
        self.calls.append({"query": query, "parameters": parameters_, "database": database_})
        if query == "RETURN 1 AS ok":
            return ([{"ok": 1}], None, None)
        return (self.records, None, None)


class FakeQdrantClient:
    def __init__(self):
        self.points = []
        self.upserts = []
        self.searches = []

    def upsert(self, collection_name, points):
        self.upserts.append({"collection_name": collection_name, "points": points})
        self.points.extend(points)

    def search(self, collection_name, query_vector, query_filter, limit):
        self.searches.append(
            {
                "collection_name": collection_name,
                "query_vector": query_vector,
                "query_filter": query_filter,
                "limit": limit,
            }
        )
        return [
            {
                "id": point["id"],
                "payload": point["payload"],
                "score": 0.9,
            }
            for point in self.points[:limit]
        ]

    def scroll(self, collection_name, scroll_filter, limit, with_payload, with_vectors):
        return (
            [
                {
                    "id": point["id"],
                    "payload": point["payload"],
                    "score": 1.0,
                }
                for point in self.points[:limit]
            ],
            None,
        )

    def get_collection(self, collection_name):
        return {"name": collection_name}
