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

Yes. Set `VORTENIX_EMAIL_PROVIDER=smtp` and the SMTP variables in your local, Git-ignored `.env`. Interactive newsletters must be explicitly approved. The separately guarded scheduled workflow can approve and send automatically.

## Why is explicit approval required?

Research output can be incomplete or misleading. Interactive workflows retain a deliberate human checkpoint. Unattended delivery is a separate explicit operational choice guarded by `VORTENIX_ALLOW_AUTOMATIC_SEND=true`, SMTP configuration, private subscriber data, and per-subscriber failure isolation.

## Can subscribers receive different research verticals?

Yes. Define each subscriber in the Git-ignored `config/subscribers.local.yaml` with their own `enabled_verticals`. `run-personalized` creates review-ready drafts. `run-scheduled` creates, automatically approves, and sends a separate newsletter to every enabled subscriber.

## Can free and premium subscribers use different research modes?

Yes. Set `research_mode: deterministic` for free subscribers and `research_mode: llm` for premium subscribers. A single personalized run builds separate shared result sets for active tiers. Premium analysis falls back independently for each failed vertical and records the requested mode, actual mode, and warnings; free subscribers never invoke the LLM.

## Does LLM mode search the internet directly?

No. Source connectors collect and normalize authorized RSS/Atom feeds and structured APIs first. The LLM receives only bounded, keyword-matched documents with `llm_allowed: true`; community sources configured as non-LLM evidence are excluded.

## Is finance content financial advice?

No. It is research information and the rendered newsletter includes that disclaimer.

## Is there a web interface or HTTP API?

No. The current interface is the Typer CLI. A review dashboard is a future roadmap phase.

## Where is generated data stored?

SQLite defaults to `data/vortenix.db`; rendered artifacts are placed in `data/newsletters/<newsletter-id>/`. Both are ignored by Git.
