# ADR-001 — Backend Framework Choice

## Status
Accepted

## Context
Phase 0 required a backend framework that could provide a fast local bootstrap, typed request/response contracts, OpenAPI generation, and low-friction route development for deterministic workflow surfaces.

## Decision
Use FastAPI as the backend framework for Phase 0.

## Consequences
Benefits:
- fast route scaffolding
- strong request/response typing with Pydantic
- built-in OpenAPI generation
- low friction for local development and testing

Tradeoffs:
- async capability exists but is not required yet
- route logic must still be kept thin to avoid workflow leakage
- contract discipline still depends on us, not the framework

## Deferred / Follow-up
- no async-specific scaling work in Phase 0
- no auth middleware integration in Phase 0
- no background task orchestration in Phase 0