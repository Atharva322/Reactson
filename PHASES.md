# Reactson Phase Tracker

## Phase 0: Reactson Foundation and Baseline

Status: completed

Acceptance gate:

- `pip install -e .`
- `import reactson`
- `reactson health`
- `pytest`

Implemented:

- Reactson Python package
- Reactson CLI and health command
- Reactson settings with `REACTSON_ENV`
- API health payload and optional FastAPI app factory
- Apache-2.0 license file
- Upstream provenance document
- Baseline tests
- CI workflow
- Baseline result note

Remaining:

- Import upstream Nexus source if supplied
- Rename migrated Nexus identifiers
- Record baseline benchmark results once benchmark fixtures exist

## Phase 1: Epistemic Memory Foundation

Status: completed

Build typed memory models, deterministic embedding wrapper, ingestion, retrieval, graph traversal, context routing, deduplication, and memory tests.

Implemented:

- Typed `ExecutionMemory`, `GraphTriple`, and `ContextItem` models
- Deterministic hash embedding service
- In-memory vector store for semantic retrieval fixtures
- In-memory graph store for relationship traversal fixtures
- Memory ingestion pipeline
- Context router with deduplication and token-budget policy
- High-level `EpistemicEngine`
- Store protocols for graph/vector backend adapters
- Neo4j graph adapter with schema validation hook
- Qdrant vector adapter with collection validation hook
- Unit tests for deterministic embeddings, task-scoped retrieval, graph neighbors, and context routing
- Adapter contract tests with fake clients

Remaining:

- External embedding provider wrapper before production memory backends are enabled
- Live Neo4j/Qdrant integration tests once local services are available

## Phase 2: Planning Framework and Complete MCTS

Status: in progress

Build `PlanningStrategy`, Linear, ReAct, MCTS node models, UCT selection, expansion, rollout, critic integration, backpropagation, budgets, cycle detection, and tree inspection.

Implemented:

- `PlanningStrategy` interface
- Typed planning request/result/transition/action models
- `LinearPlanner` baseline
- MCTS node model
- MCTS selection, expansion, rollout, reward evaluation, backpropagation, and root action selection
- Deterministic random seed support
- Tree serialization
- `ReActPlanner` baseline
- Deterministic heuristic critic with repetition and invalid-action penalties
- Planning budget clamping
- Repeated-action metadata
- Controlled benchmark helper and test showing MCTS can beat a prior-only baseline

Remaining:

- Broader cycle/repeated-action detection
- Timeout policy
- Larger benchmark comparing Linear vs ReAct vs MCTS over multiple tasks

## Phase 3: Execution, Tool Registry and MCP Synthesis

Status: pending

Separate planning from side effects with typed actions, executor, registry, router, capability gaps, sandbox validation, permissions, critic scoring, retry policy, and memory ingestion.

## Phase 4: Kernel, API, Persistence and Observability

Status: pending

Add task/session state machine, resumable state, FastAPI routes, events, cancellation, budget handling, traces, metrics, probes, and integration stack.

## Phase 5: Real-World Engineering Agent

Status: pending

Demonstrate repository diagnosis/debugging with safe repo tools, structured observations, hypotheses, evidence, and final answer synthesis.

## Phase 6: Evaluation, Reliability and Release Hardening

Status: pending

Add benchmark datasets, planner comparison reports, regression thresholds, security tests, load tests, documentation verification, and release checklist.
