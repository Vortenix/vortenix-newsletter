# Frequently asked questions

## Does the demo send email?

No. It uses the console provider, prints preview paths, and performs no external delivery.

## How do I add a vertical?

Copy a file under `config/verticals/`, set a unique ID, keywords, research areas, ranking weights that sum to approximately `1.0`, and newsletter settings. Add the ID to an audience. See the [configuration guide](docs/user-guide/configuration.md).

## How do I create a connector?

Implement the asynchronous `SourceConnector.fetch` protocol, return validated `SourceDocument` objects, and register the connector. Apply timeouts, size limits, safe logging, and offline tests. See [extension development](docs/development/extensions.md).

## Can I use another LLM?

Yes. Implement `LLMProvider.generate_structured` and update the provider factory. The workflow consumes the provider-neutral structured draft schema and retains application-owned citation validation and ranking.

## How do I disable AI?

Set `VORTENIX_RESEARCH_MODE=deterministic`, or omit it. No OpenAI key is required by deterministic mode or tests.

## Can SMTP send to my real address?

Yes. Set `VORTENIX_EMAIL_PROVIDER=smtp` and the SMTP variables in your local, Git-ignored `.env`. A newsletter must still be explicitly approved before sending.

## Why is explicit approval required?

Research output can be incomplete or misleading. Approval creates a deliberate human checkpoint and prevents generation from automatically authorising external communication.

## Can subscribers receive different research verticals?

Yes. Define each subscriber in the Git-ignored `config/subscribers.local.yaml` with their own `enabled_verticals`. Run `vortenix workflow run-personalized`; it creates a separate newsletter and recipient record for every subscriber. Each must be reviewed, approved, and sent independently.

## Can free and premium subscribers use different research modes?

Yes. Set `research_mode: deterministic` for free subscribers and `research_mode: llm` for premium subscribers. A single personalized run builds separate shared result sets for the active tiers. Premium analysis still falls back safely when API access fails.

## Is finance content financial advice?

No. It is research information and the rendered newsletter includes that disclaimer.

## Is there a web interface or HTTP API?

No. The current interface is the Typer CLI. A review dashboard is a future roadmap phase.

## Where is generated data stored?

SQLite defaults to `data/vortenix.db`; rendered artifacts are placed in `data/newsletters/<newsletter-id>/`. Both are ignored by Git.
