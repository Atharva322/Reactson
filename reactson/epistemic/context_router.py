"""Context routing and token-budget policy."""

from __future__ import annotations

from reactson.epistemic.models import ContextItem


class ContextRouter:
    def __init__(self, token_budget: int = 500) -> None:
        if token_budget <= 0:
            raise ValueError("token_budget must be positive")
        self.token_budget = token_budget

    def route(self, groups: list[list[ContextItem]]) -> list[ContextItem]:
        ranked = sorted(
            (item for group in groups for item in group),
            key=lambda item: (item.score, _source_priority(item.source)),
            reverse=True,
        )
        selected: list[ContextItem] = []
        seen_text: set[str] = set()
        used_tokens = 0

        for item in ranked:
            normalized = " ".join(item.text.lower().split())
            if normalized in seen_text:
                continue
            estimated_tokens = max(1, len(item.text.split()))
            if used_tokens + estimated_tokens > self.token_budget:
                continue
            selected.append(item)
            seen_text.add(normalized)
            used_tokens += estimated_tokens

        return selected


def _source_priority(source: str) -> int:
    priorities = {"recent": 3, "graph": 2, "vector": 1}
    return priorities.get(source, 0)
