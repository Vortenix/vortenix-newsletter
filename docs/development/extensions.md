# Extension development

## Generic vertical

Start with [`examples/minimal-vertical.yaml`](../../examples/minimal-vertical.yaml), copy it to `config/verticals/`, and add its ID to an audience. Configuration validation catches invalid weight totals.

## Specialised vertical

Implement the `ResearchVertical` protocol: expose `vertical_id`, build a `ResearchPlan`, asynchronously return a cited `VerticalResearchResult`, and rank findings. Add explicit registry construction for the implementation. Merely creating a subclass is insufficient because the current registry always chooses `GenericVertical`.

## Connector

Implement `SourceConnector.fetch(SourceRequest)`. Return normalised domain documents, isolate failures, bound time and bytes, validate URLs, avoid logging source content, and provide local fixtures. Register it in `ConnectorRegistry` and update workflow selection if needed.

## Providers

Email providers accept an `EmailMessage` and return `DeliveryResult`. LLM providers return the supplied Pydantic response model from `generate_structured`. Provider adapters must not weaken status-transition, citation, or structured-validation invariants; automatic approval belongs only to the explicitly guarded scheduled workflow.
