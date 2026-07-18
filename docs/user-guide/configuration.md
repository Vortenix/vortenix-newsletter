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
| `enabled` | boolean | `true` | Include the source |
| `retrieve_articles` | boolean | `false` | Fetch linked pages after feed parsing |

Remote requests have a 15-second timeout, three bounded attempts, exponential backoff, a user agent, and a 2 MB default body limit. The workflow uses a 24-hour lookback; demo mode substitutes the checked-in fixture and a long lookback.

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

## Provider environment variables

`VORTENIX_EMAIL_PROVIDER` selects `console` (the safe default) or `smtp`. `VORTENIX_RECIPIENTS` is a comma-separated private recipient override, keeping real addresses out of tracked audience YAML. `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, and `SMTP_USE_TLS` configure SMTP. `OPENAI_MODEL` and the standard `OPENAI_API_KEY` are consumed only when `OpenAIProvider` is constructed; LLM provider selection is not yet wired into the workflow.
