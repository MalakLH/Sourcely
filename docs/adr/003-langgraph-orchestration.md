# ADR 003: LangGraph for Agent Orchestration

## Status

Accepted

## Context

Sourcely needs an agent capable of routing
requests to specialized tools.

Some requests may eventually require
multiple tools and sequential execution.

## Decision

Use LangGraph to represent the agent
as a stateful workflow.

The graph will contain:
- Router node.
- Tool execution nodes.
- Final response node.

## Alternatives considered

1. Conventional Python if/else routing.
2. LangChain agent abstractions.
3. LangGraph StateGraph.

## Consequences

Positive:
- Explicit execution flow.
- Shared state.
- Conditional routing.
- Future multi-tool orchestration.

Negative:
- Additional framework complexity.
- Requires understanding graph state
  and execution semantics.