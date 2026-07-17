# Logging

Logging is operational metadata, not a storage channel for research bodies or secrets. The CLI configures timestamp, level, logger name, and message. Workflows log recoverable source, vertical, and finding-validation failures with identifiers and counts.

- `DEBUG`: local diagnostic details safe for developer machines.
- `INFO`: lifecycle milestones and concise command outcomes.
- `WARNING`: recoverable source, vertical, or validation failures.
- `ERROR`: an operation cannot complete.
- `CRITICAL`: process-wide integrity or availability failure.

Never log credentials, authorisation headers, complete fetched content, or full LLM prompts containing source material. Prefer stable event names and structured `extra` fields.
