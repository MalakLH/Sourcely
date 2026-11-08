# ADR 001: Monorepo and Modular Monolith

## Status

Accepted

## Context

Sourcely contains multiple related components:
an agent, documentation retrieval, web search,
sandbox execution, scanning and a ledger.

Developing all components as independent
microservices from the beginning would introduce
unnecessary infrastructure complexity.

## Decision

Use a monorepo with a modular application
architecture initially.

The agent and its tools will have clearly
separated modules and interfaces.

Services will be extracted when independent
deployment or scaling becomes necessary.

## Alternatives considered

1. Multiple repositories and microservices.
2. A monolithic application without module boundaries.
3. Monorepo with modular architecture.

## Consequences

Positive:
- Easier local development.
- Shared contracts.
- Simpler CI.
- Lower initial infrastructure overhead.

Negative:
- Repository grows over time.
- Requires clear module ownership.
- CI may need to become more selective later.