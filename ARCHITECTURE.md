# Architecture

## Philosophy

Vortenix Newsletter is a modular monolith: one deployable Python application with explicit internal boundaries. This keeps local operation, transactions, debugging, and contribution approachable while allowing mature verticals or providers to be extracted later. Extraction is an option earned by independent scaling or ownership needs, not a prerequisite.

```mermaid
flowchart TB
  CLI[CLI] --> WF[Workflows]
  WF --> ING[Ingestion]
  WF --> V[Verticals and tiered research]
  WF --> N[Newsletter]
  ING --> D[Domain contracts]
  V --> D
  N --> D
  WF --> P[Persistence repositories]
  N --> PR[Email providers]
  V --> DET[Deterministic analyser]
  V -. premium .-> LLM[LLM providers]
  LLM -. failure .-> DET
  P --> DB[(SQLite)]
```

The domain package owns vocabulary and invariants. Application workflows coordinate use cases. Adapters translate external RSS/Atom and structured APIs, email, LLM, filesystem, and database concerns. Domain models do not import SQLAlchemy or provider SDKs.

## Core contract

```mermaid
sequenceDiagram
  participant S as SourceConnector
  participant T as TierRouter
  participant D as DeterministicAnalyser
  participant L as LLMAnalyser
  participant C as Composer
  participant W as DeliveryWorkflow
  participant E as EmailProvider
  S->>T: scoped SourceDocuments
  T->>D: free subscriber verticals
  T->>L: premium subscriber verticals
  L-->>D: failed vertical fallback
  D->>C: cited results
  L->>C: cited structured results
  C->>W: personalized newsletter
  W->>E: reviewed or guarded automatic delivery
```

## Boundaries and responsibilities

| Package | Responsibility | Depends primarily on |
| --- | --- | --- |
| `domain` | Models, enums, transitions, application exceptions | Pydantic, standard library |
| `config` | YAML parsing and validation | Domain, Pydantic, PyYAML |
| `ingestion` | RSS/Atom and API collection, cleaning, provenance, canonicalisation, deduplication | Domain, HTTP/parser adapters |
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
  RSS[RSS, Atom, APIs or fixture] --> Fetch[Bounded fetch]
  Fetch --> Normalize[Clean and canonicalise]
  Normalize --> Dedup[Deduplicate]
  Dedup --> Tier{Subscriber research mode}
  Tier -->|deterministic/free| Analyse[Deterministic vertical analysis]
  Tier -->|llm/premium| AI[Bounded structured LLM analysis]
  AI -->|failure per vertical| Analyse
  AI --> Validate
  Analyse --> Validate[Validate citations and scores]
  Validate --> Rank[Weighted ranking]
  Rank --> Compose[Cross-vertical composition]
  Compose --> Render[HTML, text, JSON]
  Render --> DeliveryMode{Workflow command}
  DeliveryMode -->|run-personalized| Review[READY_FOR_REVIEW]
  DeliveryMode -->|run-scheduled and private opt-in| Auto[Automatic approval]
  Review -->|approve| Approved[APPROVED]
  Review -->|reject| Rejected[REJECTED]
  Approved --> Deliver[Email provider]
  Auto --> Deliver
```

Individual source and vertical failures are logged and treated as recoverable so remaining work can continue. Invalid configuration, persistence setup failures, and invalid state transitions are fatal to the invoked command. See [error handling](docs/development/error-handling.md).

## Extension points

```mermaid
flowchart LR
  YAML[Vertical YAML] --> Generic[GenericVertical]
  Specialized[Specialized Python class] -. implements .-> RV[ResearchVertical]
  Sources[RSS and API connectors] -. implement .-> SC[SourceConnector]
  SMTP[SMTP adapter] -. implements .-> EP[EmailProvider]
  OpenAI[OpenAI adapter] -. implements .-> LP[LLMProvider]
```

Today the vertical registry constructs generic implementations from YAML. Personalized workflows group subscribers by `research_mode`: free subscribers use deterministic analysis and premium subscribers use evidence-constrained OpenAI Structured Outputs. Premium failure falls back per vertical and is recorded in newsletter metadata. Interactive commands preserve review; unattended SMTP delivery requires a separate private opt-in and isolates subscriber failures.

## Future extraction

A module may become an independent service when it has a separate owner, deployment cadence, security boundary, or scaling profile. The extraction path is to preserve domain DTOs and provider protocols at the boundary, introduce a transport adapter, and move persistence ownership deliberately. Shared-database microservices and premature queues are explicitly avoided.

See [DECISIONS.md](DECISIONS.md) and the detailed [ADRs](docs/adr/).
