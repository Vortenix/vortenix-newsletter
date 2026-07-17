# Vortenix Newsletter implementation

## Assumptions

- This workspace is the root of the `vortenix-newsletter` repository; no extra nested directory is created.
- The repository was empty and was not initialized as a Git repository when implementation began.
- SQLite is the default persistence backend and deterministic analysis is the default research mode.
- The demo uses checked-in RSS/HTML fixtures and never accesses the network.
- Console delivery is the default. SMTP and OpenAI are optional and configured only through environment variables.
- Configuration files are authoritative for generic verticals; the four initial Python classes are thin extension points.

## Architecture plan

Build a modular monolith around domain-only Pydantic models and provider/repository protocols. Configuration and persistence sit at the edges. Ingestion produces `SourceDocument` values; registered verticals produce `VerticalResearchResult` values; validation/ranking precede composition; rendering creates review artifacts; an explicit status transition gates delivery.

## Checklist

- [x] Stage 1: metadata, configuration, domain models, database, CLI skeleton
- [x] Stage 1 validation: configuration and database smoke tests
- [x] Stage 2: connectors, RSS ingestion, cleaning, normalization, deduplication, persistence
- [x] Stage 2 validation: offline fixture ingestion tests
- [x] Stage 3: vertical registry, deterministic/optional LLM analysis, ranking, validation, persistence
- [x] Stage 3 validation: registry, weights, and deterministic workflow tests
- [x] Stage 4: selection, composition, rendering, persistence, approval
- [x] Stage 4 validation: rendered HTML, text, and JSON inspected by acceptance workflow
- [x] Stage 5: console/SMTP email, sending workflow, complete CLI
- [x] Stage 5 validation: approval gate and console provider exercised
- [x] Stage 6: fixtures, tests, README, Makefile, final validation
- [x] Acceptance commands and offline demo verified

## Progress notes

- Repository inspection: workspace empty; no `AGENTS.md`, source files, or Git metadata found.
- Python 3.13 was available locally and is compatible with the declared Python 3.12+ requirement.
- Offline demo generated all three artifacts and stopped at `READY_FOR_REVIEW`.
- Pytest, Ruff, and mypy validation completed after dependency installation.
