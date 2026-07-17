# Contributing to Vortenix Newsletter

Thank you for helping improve Vortenix Newsletter. Contributions of focused code, tests, documentation, examples, and issue triage are welcome.

## Before you start

For defects, search existing issues and open a bug report with a minimal reproduction. For a feature, open a feature request before investing in a large change. Security vulnerabilities must follow [SECURITY.md](SECURITY.md), not the public issue tracker.

## Development workflow

1. Fork the repository and create a branch from `main` named `fix/short-description`, `feature/short-description`, or `docs/short-description`.
2. Create a Python 3.12+ virtual environment and run `python -m pip install -e ".[dev]"`.
3. Make one cohesive change. Preserve domain/provider boundaries and keep business logic out of CLI handlers.
4. Add or update tests and documentation.
5. Run `make format`, `make check`, and, for workflow changes, `make demo`.
6. Open a pull request using the template.

## Style and design

- Use type hints for new public and internal APIs.
- Write concise docstrings for public classes, protocols, and functions.
- Use UTC internally and keep domain models independent of SQLAlchemy.
- Treat fetched content as untrusted and never log secrets or full source bodies.
- Add external systems behind existing protocols or a similarly narrow interface.
- Avoid new frameworks unless a documented requirement cannot be met otherwise.

Ruff is the formatter and linter; mypy checks types; pytest runs tests. The current baseline is intentionally permissive in places. New code should not copy compressed one-line formatting from early modules.

## Commits and pull requests

Use imperative, scoped commit subjects, for example `docs: explain SMTP limitation` or `fix: preserve rejected newsletter status`. Conventional Commit prefixes are encouraged but not required. Keep refactors separate from behavior changes where possible.

A pull request should explain the problem, approach, testing, documentation impact, and any security or compatibility considerations. Maintainers may request smaller commits or an ADR for a durable architectural decision. At least one maintainer approval and passing required checks are expected before merge.

## Testing and documentation expectations

Bug fixes need a regression test. New configuration needs validation tests and an entry in [the configuration reference](docs/user-guide/configuration.md). New public interfaces need [API documentation](docs/reference/public-api.md). User-facing changes require README, FAQ, or user-guide updates as appropriate.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md). Contributions are accepted under the repository's [MIT License](LICENSE).
