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

Notes:

- Pytest emitted cache-write warnings in the restricted sandbox, but test execution completed successfully.
- No upstream Nexus files were present in this workspace at scaffold time, so migration-specific rename checks are deferred until upstream source is supplied.
