# ADR 0003: Configure generic verticals with YAML

- Status: Accepted
- Date: 2026-07-18

## Context

Research areas, terms, weights, audience membership, and section limits change frequently and usually do not require new algorithms.

## Decision

Store them in human-readable YAML and validate them into typed Pydantic models before workflow execution.

## Consequences

New generic verticals require little code and configuration is reviewable in Git. YAML cannot express specialised analysis safely; those cases use Python implementations and explicit registry wiring.
