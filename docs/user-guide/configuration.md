# Configuration reference

Configuration is loaded from `config/` with PyYAML and validated by Pydantic. Paths are resolved relative to the working directory, so run commands from the repository root. The CLI loads a local, Git-ignored `.env` file for private delivery configuration.

## `application.yaml`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `database_url` | string | `sqlite:///data/vortenix.db` | SQLAlchemy database URL |
| `confidence_threshold` | float | `0.35` | Findings below this confidence are rejected |

## `sources.yaml`

Each item under `sources` accepts:

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `name` | string | required | Human-readable source name |
| `url` | string | required | HTTP(S) feed URL or local fixture path |
| `type` | connector ID | `rss` | `rss`, `reddit`, `hacker_news`, `crossref`, `fred`, or `gdelt` |
| `enabled` | boolean | `true` | Include the source |
| `retrieve_articles` | boolean | `false` | Fetch linked pages after feed parsing |
| `trust_level` | string | `industry` | Provenance tier recorded on collected documents |
| `llm_allowed` | boolean | `true` | Whether source content may be sent to the configured LLM |
| `lookback_hours` | integer | `24` | Per-source collection window (1 hour to 30 days) |
| `verticals` | list of IDs | `[]` | Restrict source evidence to selected verticals; empty means all |

Remote requests have a 15-second timeout, three bounded attempts, exponential backoff, a user agent, and a 2 MB default body limit. The workflow uses a 24-hour lookback; demo mode substitutes the checked-in fixture and a long lookback.

The production source list includes official AI, infrastructure, finance, semiconductor, security, startup, and software feeds; arXiv/Crossref research; Hacker News; GitHub releases; and GDELT discovery. The strict 24-hour default keeps each edition focused on the preceding day; quiet periods may therefore produce empty sections. Community sources are down-ranked and excluded from LLM prompts.

Reddit is configured as a disabled community-signal source. Enable it only after obtaining approved Reddit Data API credentials and setting `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and a descriptive `REDDIT_USER_AGENT`. FRED is disabled until `FRED_API_KEY` is set. `CROSSREF_MAILTO` is optional but identifies polite Crossref API usage. World Bank, IMF, OECD, Eurostat, OpenAlex, Semantic Scholar, news-search services, and licensed publishers are explicit disabled placeholders until a compliant connector or licence is configured. Disabled placeholders are never requested.

## `audiences.yaml`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `id` | string | required | Stable CLI identifier |
| `name` | string | required | Newsletter display name |
| `recipients` | list of strings | required | Delivery addresses; schema does not yet validate email syntax |
| `enabled_verticals` | list of strings | required | Vertical IDs run for the audience |
| `topic_priorities` | mapping | `{}` | Future selection preference metadata |
| `frequency` | string | `daily` | Scheduling metadata; no scheduler currently consumes it |
| `depth` | string | `detailed` | Depth metadata; not yet used by composition |
| `enabled` | boolean | `true` | Whether lookup can select the audience |

The checked-in address is deliberately a placeholder. Console delivery is the only provider selected by the current CLI.

## `verticals/*.yaml`

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `id` | string | required | Stable vertical identifier |
| `name` | string | required | Display name |
| `enabled` | boolean | `true` | Register the vertical |
| `implementation` | string | `generic` | Intent marker; registry currently constructs generic verticals |
| `research_areas` | list | `[]` | Research-plan vocabulary |
| `keywords` | list | required | Case-insensitive deterministic matching terms |
| `ranking_weights` | mapping | documented defaults | Weights for relevance, novelty, significance, evidence, recency |
| `newsletter.enabled` | boolean | conventionally `true` | Present in examples; composer does not currently filter on it |
| `newsletter.section_title` | string | vertical name | Rendered heading |
| `newsletter.maximum_items` | integer | `5` | Maximum selected findings |

Ranking weights must total within `0.01` of `1.0`. Run `vortenix config validate` after every change.

## `subscribers.local.yaml`

Copy `config/subscribers.example.yaml` to `config/subscribers.local.yaml`. The local file is ignored by Git because it contains private email addresses and preferences.

| Option | Type | Default | Meaning |
| --- | --- | --- | --- |
| `id` | string | required | Private stable subscriber identifier |
| `name` | string | required | Subscriber display name |
| `email` | string | required | Recipient used only for that subscriber's newsletter |
| `audience_id` | string | required | Parent audience that bounds available verticals |
| `enabled_verticals` | list of strings | required | Sections included for this subscriber |
| `topic_priorities` | mapping | `{}` | Subscriber-specific priority metadata |
| `frequency` | string | `daily` | Frequency metadata |
| `depth` | string | `detailed` | Depth metadata |
| `research_mode` | `deterministic` or `llm` | `deterministic` | Free or premium research tier |
| `enabled` | boolean | `true` | Include in personalized generation |

Subscriber IDs must be unique. Audience and vertical references are validated. A subscriber cannot select a vertical that is disabled for the parent audience during generation. Deterministic subscribers never invoke an LLM. LLM subscribers use structured AI analysis for their selected verticals and fall back to deterministic analysis if the provider is unavailable.

## Provider environment variables

`VORTENIX_EMAIL_PROVIDER` selects `console` (the safe default) or `smtp`. `VORTENIX_RECIPIENTS` is a comma-separated private recipient override, keeping real addresses out of tracked audience YAML. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`, and `SMTP_USE_TLS` configure SMTP. `SMTP_FROM_NAME` defaults to `Vortenix Newsletter` and controls the friendly sender name shown by email clients.

`VORTENIX_RESEARCH_MODE` selects `deterministic` (default) or `llm`. LLM mode requires `OPENAI_API_KEY`; `OPENAI_MODEL` selects the model. `VORTENIX_LLM_MAX_DOCUMENTS` defaults to `20` per vertical and `VORTENIX_LLM_MAX_DOCUMENT_CHARS` defaults to `6000` per document. See [LLM research mode](llm-research.md).
