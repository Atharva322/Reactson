from __future__ import annotations

from reactson.epistemic import EpistemicEngine, ExecutionMemory, GraphTriple
from reactson.epistemic.context_router import ContextRouter
from reactson.epistemic.embeddings import HashEmbeddingService


def test_hash_embeddings_are_deterministic() -> None:
    service = HashEmbeddingService(dimensions=16)

    assert service.embed("planner recovered failing test") == service.embed("planner recovered failing test")


def test_semantic_retrieval_is_task_scoped_and_ranked() -> None:
    engine = EpistemicEngine()
    engine.remember_episode(ExecutionMemory(task_id="task-a", text="pytest failure caused by missing import"))
    engine.remember_episode(ExecutionMemory(task_id="task-a", text="docker health check passed"))
    engine.remember_episode(ExecutionMemory(task_id="task-b", text="pytest failure in unrelated project"))

    context = engine.retrieve_context(task_id="task-a", query="missing import pytest failure", recent_limit=0)

    assert context[0].text == "pytest failure caused by missing import"
    assert all(item.task_id == "task-a" for item in context)


def test_graph_neighbors_are_retrieved_for_active_entities() -> None:
    engine = EpistemicEngine()
    engine.remember_fact(
        GraphTriple(
            task_id="task-a",
            source="Action",
            relation="PRODUCED",
            target="Observation",
            evidence="unit tests exposed a missing import",
        )
    )

    context = engine.retrieve_context(
        task_id="task-a",
        query="missing import",
        entities=("Action",),
        recent_limit=0,
        semantic_limit=0,
    )

    assert context[0].source == "graph"
    assert "Action -[PRODUCED]-> Observation" in context[0].text


def test_graph_traversal_supports_depth_greater_than_one() -> None:
    engine = EpistemicEngine()
    engine.remember_fact(GraphTriple(task_id="task-a", source="Task", relation="HAS_HYPOTHESIS", target="Hypothesis"))
    engine.remember_fact(GraphTriple(task_id="task-a", source="Hypothesis", relation="SUPPORTED_BY", target="Evidence"))

    context = engine.retrieve_context(
        task_id="task-a",
        query="evidence",
        entities=("Task",),
        recent_limit=0,
        semantic_limit=0,
        graph_depth=2,
    )

    assert [item.text for item in context] == [
        "Task -[HAS_HYPOTHESIS]-> Hypothesis",
        "Hypothesis -[SUPPORTED_BY]-> Evidence",
    ]


def test_context_router_deduplicates_and_respects_budget() -> None:
    router = ContextRouter(token_budget=5)
    first = ExecutionMemory(task_id="task-a", text="alpha beta").text
    duplicate = ExecutionMemory(task_id="task-a", text="alpha beta").text
    long_text = ExecutionMemory(task_id="task-a", text="one two three four five six").text

    routed = router.route(
        [
            [
                _item(first, "recent", 0.9),
                _item(duplicate, "vector", 1.0),
                _item(long_text, "vector", 0.8),
            ]
        ]
    )

    assert [item.text for item in routed] == ["alpha beta"]


def _item(text: str, source: str, score: float):
    from reactson.epistemic.models import ContextItem

    return ContextItem(text=text, source=source, score=score, task_id="task-a")
