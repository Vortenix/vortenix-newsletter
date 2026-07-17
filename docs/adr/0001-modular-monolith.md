# ADR 0001: Use a modular monolith

- Status: Accepted
- Date: 2026-07-18

## Context

The project spans ingestion, research, composition, review, persistence, and delivery, but has one small team and no demonstrated independent scaling needs.

## Decision

Ship one Python application with explicit package boundaries and domain contracts. Do not introduce distributed messaging or independently deployed services.

## Consequences

Installation, transactions, local debugging, and testing remain simple. Contributors must preserve dependency direction because process boundaries do not enforce it. A module may be extracted when ownership, security, release cadence, or scaling evidence justifies the operational cost.
