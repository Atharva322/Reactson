"""Graph memory store contracts and in-memory implementation."""

from __future__ import annotations

from collections import defaultdict, deque

from reactson.epistemic.models import ContextItem, GraphTriple


class InMemoryGraphStore:
    def __init__(self) -> None:
        self._triples: list[GraphTriple] = []
        self._by_source: dict[tuple[str, str], list[GraphTriple]] = defaultdict(list)

    def add(self, triple: GraphTriple) -> None:
        self._triples.append(triple)
        self._by_source[(triple.task_id, triple.source.lower())].append(triple)

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
