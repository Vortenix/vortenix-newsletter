# Changelog

All notable changes are documented here. This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and intends to use [Semantic Versioning](https://semver.org/) from its first stable release.

## [Unreleased]

### Added

- Private, Git-ignored subscriber profiles with independent vertical selections.
- Shared research execution with one separately reviewable newsletter per subscriber.
- Personalized recipient persistence and CLI commands for subscriber listing and generation.
- Optional evidence-constrained OpenAI Structured Outputs with bounded inputs and deterministic fallback.
- Per-subscriber deterministic (free) and LLM (premium) research tiers.
- Requested-versus-actual analysis metadata and visible premium fallback warnings.
- Expanded RSS/Atom and structured API ingestion with provenance and vertical scoping.
- Guarded unattended per-subscriber delivery and GitHub Actions scheduling.

### Changed

- Email subjects now use `Vortenix Newsletter - Daily Research Brief - YYYY-MM-DD`.
- SMTP messages include a friendly sender name, date, and unique message ID.
- Free subscribers use deterministic analysis; premium subscribers request LLM analysis with per-vertical deterministic fallback.

## [0.2.0] - 2026-07-18

### Added

- Open-source community standards, architecture documentation, examples, and CI workflows.
- Offline deterministic research, cited newsletter rendering, review workflow, and console delivery.
- RSS ingestion, YAML vertical configuration, SQLite persistence, and provider protocols.
- Local, Git-ignored SMTP provider and recipient selection.

### Known limitations at release

- At the 0.2.0 release, OpenAI analysis was not yet selected by the workflow; this is resolved in Unreleased.
- Test coverage and strict typing are still being expanded.

## [0.1.0] - 2026-07-18

### Added

- Initial working modular-monolith implementation and offline demonstration.

[Unreleased]: https://github.com/vortenix/vortenix-newsletter/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/vortenix/vortenix-newsletter/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/vortenix/vortenix-newsletter/releases/tag/v0.1.0
