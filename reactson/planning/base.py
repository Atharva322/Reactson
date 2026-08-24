"""Planning strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from reactson.planning.models import PlanRequest, PlanResult, Transition


class PlanningStrategy(ABC):
    @abstractmethod
    async def propose(self, request: PlanRequest) -> PlanResult:
        ...

    @abstractmethod
    async def update(self, transition: Transition) -> None:
        ...
