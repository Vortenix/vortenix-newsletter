# Public Python API

The CLI is the primary supported interface. The protocols below are the intended extension surface; other Python modules may change during the `0.x` series.

## `SourceConnector`

`async fetch(request: SourceRequest) -> list[SourceDocument]` collects and normalises source records. Implementations must return independent domain objects and isolate external I/O.

## `ResearchVertical`

`vertical_id`, `build_research_plan`, `analyse`, and `rank_findings` separate topic logic from newsletter code. Findings must contain citations and bounded component scores.

## `EmailProvider`

`async send(message: EmailMessage) -> DeliveryResult` performs delivery. Callers enforce approval before invocation; providers report structured success or failure.

## `LLMProvider`

`async generate_structured(system_prompt, user_prompt, response_model) -> T` returns a validated Pydantic model. Implementations must use only supplied evidence and preserve document IDs in citations.

## Repositories

`SourceRepository`, `ResultRepository`, and `NewsletterRepository` provide current SQLite-backed persistence operations. They are concrete classes, not formal public protocols. `NewsletterRepository.save/get/list` is used by approval and delivery services.
