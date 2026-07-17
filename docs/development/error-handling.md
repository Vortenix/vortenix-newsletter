# Error handling

Recoverable failures allow useful partial output: one malformed feed entry is skipped; one source or vertical failure is logged while others continue; individual invalid findings are excluded.

Fatal failures stop the command: invalid YAML/Pydantic configuration, database setup errors, an unknown audience, missing newsletter artifacts, or an invalid status transition. CLI error presentation is currently basic and may include a traceback; improving it without hiding diagnostics is roadmap work.

Application exceptions live in `domain.exceptions`. Adapters should translate provider-specific exceptions into useful application results or exceptions without exposing secrets.
