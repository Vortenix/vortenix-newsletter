# LLM research mode

LLM mode is an optional analysis layer over configured source documents. It does not search the web and does not replace RSS ingestion, validation, ranking, review, or approval.

For personalized newsletters, mode is selected per subscriber: `research_mode: deterministic` is the free tier and `research_mode: llm` is the premium tier. The global `VORTENIX_RESEARCH_MODE` continues to control non-personalized audience-level runs.

## Setup

Install the optional SDK:

```console
python -m pip install -e ".[openai,dev]"
```

Set private values in the Git-ignored `.env`:

```dotenv
VORTENIX_RESEARCH_MODE=llm
OPENAI_API_KEY=your-project-api-key
OPENAI_MODEL=gpt-4.1-mini
VORTENIX_LLM_MAX_DOCUMENTS=20
VORTENIX_LLM_MAX_DOCUMENT_CHARS=6000
```

Never place a real key in `.env.example`, YAML, source code, tests, logs, or GitHub. API usage may incur charges.

## Evidence and safety behavior

For each vertical, the analyser selects recent documents matching configured keywords and caps their number and character length. Source text is labelled untrusted evidence. The system prompt requires the model to use only supplied documents, distinguish observation from interpretation, avoid financial advice, and cite supplied document IDs.

The model returns a provider-neutral Pydantic draft. Application code then:

1. Rejects findings without citations or with unknown document IDs.
2. Builds source titles and URLs from trusted local documents rather than model output.
3. Calculates relevance, evidence, recency, confidence, and weighted rank outside the model.
4. Runs the existing finding validator.
5. Falls back to deterministic analysis for that vertical if provider construction, API access, parsing, or analysis fails.

The OpenAI request uses structured output parsing and `store=False`. Source content is still transmitted to the configured API provider; only enable LLM mode for material you are authorized to process.

Every newsletter records both `research_mode` (the subscriber's requested tier) and `analysis_mode` (what actually produced the findings). When one or more premium verticals fall back, `analysis_mode` becomes `deterministic` or `mixed` and `analysis_warnings` identifies the affected verticals. Review these fields before approving premium delivery.

## Operation

Use the normal workflows:

```console
vortenix workflow run-personalized --audience anish_daily
```

Logs identify fallback events but never include the API key, full source bodies, or prompts. To disable external AI calls immediately, set:

```dotenv
VORTENIX_RESEARCH_MODE=deterministic
```

Tests inject fake providers and make no paid API calls.
