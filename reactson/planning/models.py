"""Planning model types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from uuid import uuid4


@dataclass(frozen=True)
class ActionCandidate:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    prior_score: float = 0.0


@dataclass(frozen=True)
class PlanRequest:
    state: Any
    context: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    budget: int | None = None


@dataclass(frozen=True)
class PlanResult:
    action: ActionCandidate | None
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Transition:
    state_before: Any
    action: ActionCandidate
    state_after: Any
    reward: float
    terminal: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCTSNode:
    state_snapshot: Any
    node_id: str = field(default_factory=lambda: str(uuid4()))
    parent_id: str | None = None
    action: ActionCandidate | None = None
    children: list["MCTSNode"] = field(default_factory=list)
    visits: int = 0
    total_value: float = 0.0
    prior_score: float = 0.0
    terminal: bool = False
    depth: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def mean_reward(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.total_value / self.visits

    def serialize(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "parent_id": self.parent_id,
            "state_snapshot": self.state_snapshot,
            "action": self.action.name if self.action else None,
            "children": [child.serialize() for child in self.children],
            "visits": self.visits,
            "total_value": self.total_value,
            "mean_reward": self.mean_reward,
            "prior_score": self.prior_score,
            "terminal": self.terminal,
            "depth": self.depth,
            "metadata": self.metadata,
        }


class PlanningEnvironment(Protocol):
    def actions(self, state: Any, context: tuple[str, ...], tools: tuple[str, ...]) -> list[ActionCandidate]:
        ...

    def transition(self, state: Any, action: ActionCandidate) -> Any:
        ...

    def reward(self, state: Any) -> float:
        ...

    def is_terminal(self, state: Any) -> bool:
        ...
