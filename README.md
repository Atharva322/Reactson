# Reactson

Reactson is an incremental implementation of a self-evolving AI agent runtime for long-horizon engineering and systems tasks.

The project is being built phase by phase from the architecture and implementation roadmap:

1. Reactson foundation and baseline
2. Epistemic memory foundation
3. Planning framework and complete MCTS
4. Execution, tool registry and MCP synthesis
5. Kernel, API, persistence and observability
6. Real-world engineering agent
7. Evaluation, reliability and release hardening

## Current Status

Phase 0 is complete. Phase 1 is in progress with deterministic in-memory memory stores, typed models, ingestion, retrieval, graph traversal, context routing, Neo4j/Qdrant adapter contracts, and tests.

## Quick Start

```bash
pip install -e .
python -c "import reactson; print(reactson.__version__)"
reactson health
pytest
```

## CLI

```bash
reactson health
reactson version
reactson phases
```

## API

The API module exposes a FastAPI app when FastAPI is installed:

```python
from reactson.api.app import create_app

app = create_app()
```

The health contract is also available without optional API dependencies:

```python
from reactson.api.app import health_payload
```

## License and Provenance

Reactson is derived from the Apache-2.0 licensed Nexus project. See [UPSTREAM.md](UPSTREAM.md) and [LICENSE](LICENSE).
