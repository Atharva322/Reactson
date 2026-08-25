# Phase 0 Baseline Results

Date: 2026-08-24

Environment:

- OS: Windows
- Python: 3.12.5
- Test runner: pytest 8.3.4

Gate results:

- `python -m pip install -e .`: pass after running outside the restricted sandbox because pip needed user temp and site-package write access.
- `python -c "import reactson; print(reactson.__version__)"`: pass, printed `0.1.0`.
- `python -m reactson.cli health`: pass, returned Reactson health JSON.
- `pytest`: pass, 5 tests passed.

Phase 1 progress check:

- `pytest -q`: pass, 12 tests passed after adding memory store interfaces, deterministic stores, graph/vector adapter contracts, and context-routing coverage.

Phase 2 progress check:

- `pytest -q`: pass, 20 tests passed after adding ReAct, critic, budget, and benchmark coverage.

Phase 3 progress check:

- `pytest -q`: pass, 33 tests passed after completing synthesizer, sandbox, retry, and memory-ingestion coverage.

Phase 4 progress check:

- `pytest -q`: pass, 41 tests passed after adding metrics, tracing, readiness, event filtering, and budget handling.
- `pytest -q`: pass, 44 tests passed after completing task listing, event cursors, JSONL streams, and persistence readiness.

Notes:

- Pytest emitted cache-write warnings in the restricted sandbox, but test execution completed successfully.
- No upstream Nexus files were present in this workspace at scaffold time, so migration-specific rename checks are deferred until upstream source is supplied.
