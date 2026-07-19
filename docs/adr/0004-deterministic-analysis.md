# ADR 0004: Make deterministic analysis the baseline

- Status: Accepted
- Date: 2026-07-18

## Context

The project must work without credentials, internet access, variable model output, or paid dependencies.

## Decision

Use keyword matching, extractive summaries, heuristics, component scoring, and citations as the default analysis path. Keep LLM analysis optional and structured.

## Consequences

The demo is reproducible and tests have a stable oracle. Heuristic entity and pain-point quality is limited. Optional LLM output must still pass domain validation and never replaces application-owned ranking or status transitions. Personalized free subscribers use this deterministic path directly; premium subscribers fall back to it per vertical when LLM analysis fails.
