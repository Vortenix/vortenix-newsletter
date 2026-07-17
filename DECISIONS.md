# Architectural decisions

This index summarises decisions that shape the project. Detailed records are under [`docs/adr`](docs/adr/).

## Modular monolith

A single application is easier to install, test, transact, and operate for the current team and workload. Internal packages retain boundaries needed for later extraction. See [ADR 0001](docs/adr/0001-modular-monolith.md).

## Provider abstraction

RSS, LLM, and email systems sit behind narrow protocols so the domain does not depend on vendor SDKs. This enables offline tests and avoids paid required dependencies. See [ADR 0002](docs/adr/0002-provider-abstraction.md).

## YAML configuration

Research vocabulary changes more often than core orchestration. Validated YAML lets maintainers add generic verticals and audiences without application code while keeping errors visible at startup. See [ADR 0003](docs/adr/0003-yaml-configuration.md).

## Deterministic analysis

The baseline must work without credentials, network access, or probabilistic output. Deterministic analysis provides a reproducible fallback and test oracle. See [ADR 0004](docs/adr/0004-deterministic-analysis.md).

## Repository separation

Domain models remain independent from SQLAlchemy records. Repositories centralise mapping and query operations, preventing storage concerns from leaking into workflows. Formal protocols can be added when multiple implementations clarify the necessary abstraction.

## Explicit approval

Generation never implies permission to communicate externally. A newsletter must transition from `READY_FOR_REVIEW` to `APPROVED` before delivery. Rejected newsletters cannot be sent. This is a safety and editorial-control invariant, not merely a UI convention.
