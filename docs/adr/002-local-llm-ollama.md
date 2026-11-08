# ADR 002: Ollama for Local LLM Inference

## Status

Accepted

## Context

Sourcely must operate without depending
on paid external LLM APIs.

Local inference is required for development
and reproducible experimentation.

## Decision

Use Ollama as the local inference runtime.

Evaluate multiple models based on:
- Tool calling reliability.
- Routing accuracy.
- Latency.
- Memory consumption.

The final model will be selected based
on experimental results.

## Alternatives considered

1. Cloud-hosted LLM APIs.
2. Direct model serving infrastructure.
3. Ollama.

## Consequences

Positive:
- Local inference.
- Reduced external API dependency.
- Easy model experimentation.

Negative:
- Hardware requirements.
- Model-specific tool-calling behavior.
- Local inference latency.