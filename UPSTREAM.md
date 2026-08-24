# Upstream Provenance

Reactson is derived from the Apache-2.0 licensed Nexus project.

## Current Import Status

This repository currently contains a clean Reactson Phase 0 foundation. No upstream Nexus source files were present in the workspace when the foundation was created, so no line-level migration has been performed yet.

## Required Preservation Rules

- Preserve Apache-2.0 license notices from any upstream Nexus files copied into this repository.
- Keep this file updated with upstream source references, copied commit SHAs, and major changes.
- Prefer additive Reactson changes during migration until baseline tests pass.

## Major Reactson Changes

- Established Reactson package identity and CLI names.
- Added initial configuration using `REACTSON_ENV`.
- Added baseline health contract for CLI and API use.
- Added phase roadmap tracking for incremental delivery.
