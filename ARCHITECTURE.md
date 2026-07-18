# Architecture

## Philosophy

Vortenix Newsletter is a modular monolith: one deployable Python application with explicit internal boundaries. This keeps local operation, transactions, debugging, and contribution approachable while allowing mature verticals or providers to be extracted later. Extraction is an option earned by independent scaling or ownership needs, not a prerequisite.

```mermaid
flowchart TB
  CLI[CLI] --> WF[Workflows]
  WF --> ING[Ingestion]
  WF --> V[Verticals and research]
  WF --> N[Newsletter]
  ING --> D[Domain contracts]
  V --> D
  N --> D
  WF --> P[Persistence repositories]
  N --> PR[Email providers]
  V -. optional .-> LLM[LLM providers]
  P --> DB[(SQLite)]
```

The domain package owns vocabulary and invariants. Application workflows coordinate use cases. Adapters translate external RSS, email, LLM, filesystem, and database concerns. Domain models do not import SQLAlchemy or provider SDKs.

## Core contract

```mermaid
sequenceDiagram
  participant S as SourceConnector
  participant V as ResearchVertical
  participant C as Composer
  participant R as Reviewer
  participant E as EmailProvider
  S->>V: list[SourceDocument]
  V->>C: VerticalResearchResult
  C->>R: Newsletter (READY_FOR_REVIEW)
  R->>R: explicit approval
  R->>E: EmailMessage
```

## Boundaries and responsibilities

| Package | Responsibility | Depends primarily on |
| --- | --- | --- |
| `domain` | Models, enums, transitions, application exceptions | Pydantic, standard library |
| `config` | YAML parsing and validation | Domain, Pydantic, PyYAML |
| `ingestion` | RSS fetching, cleaning, canonicalisation, deduplication | Domain, HTTP/parser adapters |
| `verticals` | Research plans and vertical implementations | Domain, config, ranking |
| `research` | Explainable ranking and evidence validation | Domain, config |
| `newsletter` | Selection, composition, rendering, approval/delivery service | Domain, templates, provider contract |
| `persistence` | SQLAlchemy records and repositories | Domain, SQLAlchemy |
| `providers` | Console/SMTP and deterministic/OpenAI adapters | Domain and optional SDKs |
| `workflows` | End-to-end application orchestration and fault isolation | Application packages |
| `cli` | User input/output and process entry point | Workflows and services |

## Dependency direction

```mermaid
flowchart LR
  CLI --> Workflows
  Workflows --> Ingestion
  Workflows --> Research
  Workflows --> Newsletter
  Workflows --> Persistence
  Ingestion --> Domain
  Research --> Domain
  Newsletter --> Domain
  Persistence --> Domain
  Providers --> Domain
```

Provider and repository implementations are replaceable edges. The current code has concrete repository classes rather than formal repository protocols; introducing protocols should happen when a second persistence implementation makes the contract concrete.

## Workflow and failure model

```mermaid
flowchart TD
  RSS[RSS or offline fixture] --> Fetch[Bounded fetch]
  Fetch --> Normalize[Clean and canonicalise]
  Normalize --> Dedup[Deduplicate]
  Dedup --> Match[Keyword classification]
  Match --> Analyse[Vertical analysis]
  Analyse --> Validate[Validate citations and scores]
  Validate --> Rank[Weighted ranking]
  Rank --> Compose[Cross-vertical composition]
  Compose --> Render[HTML, text, JSON]
  Render --> Review[READY_FOR_REVIEW]
  Review -->|approve| Approved[APPROVED]
  Review -->|reject| Rejected[REJECTED]
  Approved --> Deliver[Email provider]
```

Individual source and vertical failures are logged and treated as recoverable so remaining work can continue. Invalid configuration, persistence setup failures, and invalid state transitions are fatal to the invoked command. See [error handling](docs/development/error-handling.md).

## Extension points

```mermaid
flowchart LR
  YAML[Vertical YAML] --> Generic[GenericVertical]
  Specialized[Specialized Python class] -. implements .-> RV[ResearchVertical]
  RSS[RSSConnector] -. implements .-> SC[SourceConnector]
  SMTP[SMTP adapter] -. implements .-> EP[EmailProvider]
  OpenAI[OpenAI adapter] -. implements .-> LP[LLMProvider]
```

Today the vertical registry constructs generic implementations from YAML. Specialized classes exist as evolution points but need explicit registry wiring before use. The CLI selects console or SMTP delivery from local environment configuration. Research mode selects deterministic analysis or evidence-constrained OpenAI Structured Outputs with per-vertical deterministic fallback.

## Future extraction

A module may become an independent service when it has a separate owner, deployment cadence, security boundary, or scaling profile. The extraction path is to preserve domain DTOs and provider protocols at the boundary, introduce a transport adapter, and move persistence ownership deliberately. Shared-database microservices and premature queues are explicitly avoided.

See [DECISIONS.md](DECISIONS.md) and the detailed [ADRs](docs/adr/).
