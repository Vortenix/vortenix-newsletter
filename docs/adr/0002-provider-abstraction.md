# ADR 0002: Isolate external providers

- Status: Accepted
- Date: 2026-07-18

## Context

Source, email, and LLM vendors have distinct credentials, failure modes, SDKs, and costs. Tests and the demo must be offline.

## Decision

Define narrow protocols using domain request/result types and implement vendor adapters at the edge.

## Consequences

Core logic is testable without external services and paid services remain optional. Selection and configuration still require deliberate application wiring; the existence of an adapter does not mean the workflow uses it.
