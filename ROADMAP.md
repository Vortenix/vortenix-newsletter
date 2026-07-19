# Roadmap

The roadmap communicates direction, not a delivery commitment. Priorities may change based on contributor feedback and operational evidence.

## Completed foundation

- [x] Multi-source ingestion, deterministic research, citations, rendering, review, and SQLite persistence.
- [x] Secure console/SMTP provider selection and private subscriber configuration.
- [x] Personalized free deterministic and premium LLM tiers with per-vertical deterministic fallback.
- [x] Guarded unattended delivery and timezone-aware GitHub Actions scheduling.
- [x] RSS/Atom and structured API connectors with provenance, licensing, and rate-limit controls.

## Current priorities

- Replace best-effort GitHub cron with durable cloud scheduling and delivery idempotency.
- Improve company/entity heuristics, cross-source corroboration, and cross-vertical deduplication.
- Add ingestion and delivery observability without logging private content.
- Complete migration infrastructure and repository interfaces.
- Expand integration, failure-path, SMTP, rendering, and scheduler tests.

## Review dashboard

- Introduce an optional review API and accessible dashboard.
- Support editing, evidence inspection, audit history, and role-based approval.

## Publishing channels

- Add opt-in social and web publishing providers.
- Preserve per-channel approval, previews, and delivery audits.

## Technology knowledge graph

- Model durable relationships between developments, technologies, companies, and evidence.
- Adopt specialised storage only after query and scale requirements are demonstrated.

## Independent research services

- Extract verticals that require independent teams, deployment, or scaling.
- Keep interoperable research result contracts and avoid shared database ownership.
