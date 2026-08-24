"""Monte Carlo Tree Search planning strategy."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

from reactson.planning.base import PlanningStrategy
from reactson.planning.critic import HeuristicCritic
from reactson.planning.models import (
    ActionCandidate,
    MCTSNode,
    PlanRequest,
    PlanResult,
    PlanningEnvironment,
    Transition,
)


@dataclass(frozen=True)
class MCTSConfig:
    simulations: int = 32
    exploration_constant: float = 1.4
    max_depth: int = 8
    rollout_depth: int = 4
    random_seed: int = 0


class MCTSPlanner(PlanningStrategy):
    def __init__(self, environment: PlanningEnvironment, config: MCTSConfig | None = None) -> None:
        self.environment = environment
        self.config = config or MCTSConfig()
        if self.config.simulations <= 0:
            raise ValueError("simulations must be positive")
        if self.config.max_depth <= 0:
            raise ValueError("max_depth must be positive")
        if self.config.rollout_depth <= 0:
            raise ValueError("rollout_depth must be positive")
        self.random = random.Random(self.config.random_seed)
        self.critic = HeuristicCritic(environment)
        self.root: MCTSNode | None = None
        self.transitions: list[Transition] = []
        self.repeated_actions = 0

    async def propose(self, request: PlanRequest) -> PlanResult:
        simulation_count = self._simulation_count(request)
        self.repeated_actions = 0
        self.root = MCTSNode(
            state_snapshot=request.state,
            terminal=self.environment.is_terminal(request.state),
            metadata={"planner": "mcts"},
        )

        for _ in range(simulation_count):
            path = [self.root]
            leaf = self._select(self.root, path, request)
            expanded = self._expand(leaf, request)
            if expanded is not leaf:
                path.append(expanded)
            reward = self._rollout(expanded.state_snapshot, request, expanded.depth)
            self._backpropagate(path, reward)

        if not self.root.children:
            return PlanResult(action=None, score=self.root.mean_reward, metadata=self._metadata())

        best = max(self.root.children, key=lambda child: (child.mean_reward, child.visits, child.prior_score))
        return PlanResult(
            action=best.action,
            score=best.mean_reward,
            metadata=self._metadata(root_action=best.action.name if best.action else None),
        )

    async def update(self, transition: Transition) -> None:
        self.transitions.append(transition)

    def tree(self) -> dict[str, Any]:
        if self.root is None:
            return {}
        return self.root.serialize()

    def _select(self, node: MCTSNode, path: list[MCTSNode], request: PlanRequest) -> MCTSNode:
        current = node
        while current.children and not current.terminal and current.depth < self.config.max_depth:
            if not self._fully_expanded(current, request):
                return current
            current = max(current.children, key=lambda child: self._uct(current, child))
            path.append(current)
            if current.visits == 0:
                break
        return current

    def _expand(self, node: MCTSNode, request: PlanRequest) -> MCTSNode:
        if node.terminal or node.depth >= self.config.max_depth:
            return node

        existing_actions = {child.action.name for child in node.children if child.action is not None}
        actions = [
            action
            for action in self.environment.actions(node.state_snapshot, request.context, request.tools)
            if action.name not in existing_actions and not self._would_cycle(node, action)
        ]
        if not actions:
            return node

        action = max(actions, key=lambda candidate: (candidate.prior_score, candidate.name))
        next_state = self.environment.transition(node.state_snapshot, action)
        child = MCTSNode(
            state_snapshot=next_state,
            parent_id=node.node_id,
            action=action,
            prior_score=action.prior_score,
            terminal=self.environment.is_terminal(next_state),
            depth=node.depth + 1,
        )
        node.children.append(child)
        return child

    def _rollout(self, state: Any, request: PlanRequest, depth: int) -> float:
        current_state = state
        current_depth = depth
        seen_actions: set[tuple[str, str]] = set()
        last_critique = None

        while current_depth < self.config.max_depth and current_depth - depth < self.config.rollout_depth:
            if self.environment.is_terminal(current_state):
                break
            actions = self.environment.actions(current_state, request.context, request.tools)
            if not actions:
                break
            action = self._choose_rollout_action(actions)
            state_before = current_state
            current_state = self.environment.transition(current_state, action)
            last_critique = self.critic.evaluate(
                state_before=state_before,
                action=action,
                state_after=current_state,
                seen_actions=seen_actions,
            )
            repeated_key = (repr(state_before), action.name)
            if repeated_key in seen_actions:
                self.repeated_actions += 1
            seen_actions.add(repeated_key)
            current_depth += 1

        if last_critique is not None:
            return last_critique.reward
        return self.environment.reward(current_state)

    def _choose_rollout_action(self, actions: list[ActionCandidate]) -> ActionCandidate:
        ordered = sorted(actions, key=lambda candidate: candidate.name)
        best_prior = max(action.prior_score for action in ordered)
        best_actions = [action for action in ordered if action.prior_score == best_prior]
        return self.random.choice(best_actions)

    def _backpropagate(self, path: list[MCTSNode], reward: float) -> None:
        for node in path:
            node.visits += 1
            node.total_value += reward

    def _uct(self, parent: MCTSNode, child: MCTSNode) -> float:
        if child.visits == 0:
            return math.inf
        exploitation = child.mean_reward
        exploration = self.config.exploration_constant * math.sqrt(math.log(max(parent.visits, 1)) / child.visits)
        return exploitation + exploration + child.prior_score

    def _would_cycle(self, node: MCTSNode, action: ActionCandidate) -> bool:
        seen_states = set()
        current: MCTSNode | None = node
        while current is not None:
            seen_states.add(repr(current.state_snapshot))
            current = _find_parent(self.root, current.parent_id) if self.root is not None else None
        target_state = repr(self.environment.transition(node.state_snapshot, action))
        return target_state in seen_states

    def _simulation_count(self, request: PlanRequest) -> int:
        if request.budget is None:
            return self.config.simulations
        return max(1, min(request.budget, self.config.simulations))

    def _fully_expanded(self, node: MCTSNode, request: PlanRequest) -> bool:
        existing_actions = {child.action.name for child in node.children if child.action is not None}
        valid_actions = {
            action.name
            for action in self.environment.actions(node.state_snapshot, request.context, request.tools)
            if not self._would_cycle(node, action)
        }
        return valid_actions.issubset(existing_actions)

    def _metadata(self, root_action: str | None = None) -> dict[str, Any]:
        root = self.root
        if root is None:
            return {"planner": "mcts"}
        return {
            "planner": "mcts",
            "root_action": root_action,
            "simulations": root.visits,
            "nodes_expanded": _count_nodes(root),
            "tree_depth": _max_depth(root),
            "repeated_actions": self.repeated_actions,
            "tree": root.serialize(),
        }


def _count_nodes(node: MCTSNode) -> int:
    return 1 + sum(_count_nodes(child) for child in node.children)


def _max_depth(node: MCTSNode) -> int:
    if not node.children:
        return node.depth
    return max(_max_depth(child) for child in node.children)


def _find_parent(root: MCTSNode, parent_id: str | None) -> MCTSNode | None:
    if parent_id is None:
        return None
    if root.node_id == parent_id:
        return root
    for child in root.children:
        found = _find_parent(child, parent_id)
        if found is not None:
            return found
    return None
