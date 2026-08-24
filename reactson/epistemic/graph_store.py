"""Graph memory store implementations."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from reactson.epistemic.errors import MemoryStoreConfigurationError
from reactson.epistemic.models import ContextItem, GraphTriple


class InMemoryGraphStore:
    def __init__(self) -> None:
        self._triples: list[GraphTriple] = []
        self._by_source: dict[tuple[str, str], list[GraphTriple]] = defaultdict(list)

    def add(self, triple: GraphTriple) -> None:
        self._triples.append(triple)
        self._by_source[(triple.task_id, triple.source.lower())].append(triple)

    def validate_schema(self) -> bool:
        return True

    def neighbors(self, task_id: str, entity: str, depth: int = 1, limit: int = 10) -> list[ContextItem]:
        if depth <= 0 or limit <= 0:
            return []

        seen_entities = {entity.lower()}
        queue: deque[tuple[str, int]] = deque([(entity, 0)])
        results: list[ContextItem] = []

        while queue and len(results) < limit:
            current, current_depth = queue.popleft()
            if current_depth >= depth:
                continue

            for triple in self._by_source.get((task_id, current.lower()), []):
                text = f"{triple.source} -[{triple.relation}]-> {triple.target}"
                if triple.evidence:
                    text = f"{text}. Evidence: {triple.evidence}"
                results.append(
                    ContextItem(
                        text=text,
                        source="graph",
                        score=1.0 / (current_depth + 1),
                        task_id=triple.task_id,
                        metadata=triple.metadata,
                    )
                )
                target_key = triple.target.lower()
                if target_key not in seen_entities:
                    seen_entities.add(target_key)
                    queue.append((triple.target, current_depth + 1))
                if len(results) >= limit:
                    break

        return results


class Neo4jGraphStore:
    """Neo4j graph store adapter.

    The constructor accepts a driver-like object for tests. Use
    `from_connection` in production code after installing the `memory` extra.
    """

    def __init__(self, driver: Any, database: str | None = None) -> None:
        self.driver = driver
        self.database = database

    @classmethod
    def from_connection(
        cls,
        *,
        uri: str,
        username: str,
        password: str,
        database: str | None = None,
    ) -> "Neo4jGraphStore":
        try:
            from neo4j import GraphDatabase
        except ImportError as exc:
            raise MemoryStoreConfigurationError(
                "Install Reactson with the 'memory' extra to use Neo4jGraphStore."
            ) from exc

        return cls(GraphDatabase.driver(uri, auth=(username, password)), database=database)

    def add(self, triple: GraphTriple) -> None:
        query = """
        MERGE (source:Entity {name: $source, task_id: $task_id})
        MERGE (target:Entity {name: $target, task_id: $task_id})
        MERGE (source)-[edge:RELATED {relation: $relation}]->(target)
        SET edge.evidence = $evidence,
            edge.metadata = $metadata
        """
        self._execute(
            query,
            source=triple.source,
            relation=triple.relation,
            target=triple.target,
            task_id=triple.task_id,
            evidence=triple.evidence,
            metadata=triple.metadata,
        )

    def neighbors(self, task_id: str, entity: str, depth: int = 1, limit: int = 10) -> list[ContextItem]:
        safe_depth = max(1, int(depth))
        safe_limit = max(1, int(limit))
        query = """
        MATCH path = (:Entity {name: $entity, task_id: $task_id})-[edges:RELATED*1..%d]->(target:Entity)
        UNWIND relationships(path) AS edge
        WITH edge, startNode(edge) AS source, endNode(edge) AS target
        RETURN source.name AS source,
               edge.relation AS relation,
               target.name AS target,
               edge.evidence AS evidence,
               edge.metadata AS metadata
        LIMIT $limit
        """ % safe_depth
        records = self._execute(query, entity=entity, task_id=task_id, limit=safe_limit)
        items: list[ContextItem] = []
        for record in records:
            text = f"{record['source']} -[{record['relation']}]-> {record['target']}"
            if record.get("evidence"):
                text = f"{text}. Evidence: {record['evidence']}"
            items.append(
                ContextItem(
                    text=text,
                    source="graph",
                    score=1.0,
                    task_id=task_id,
                    metadata=record.get("metadata") or {},
                )
            )
        return items

    def validate_schema(self) -> bool:
        query = "RETURN 1 AS ok"
        records = self._execute(query)
        return bool(records)

    def _execute(self, query: str, **parameters: Any) -> list[Any]:
        if hasattr(self.driver, "execute_query"):
            result = self.driver.execute_query(query, parameters_=parameters, database_=self.database)
            records = result[0] if isinstance(result, tuple) else result
            return list(records)

        with self.driver.session(database=self.database) as session:
            return list(session.run(query, **parameters))
