# ADR-007 — Shared Type Strategy

## Status
Accepted

## Context
Phase 0 needed type consistency across backend and frontend, but full shared-code generation would add complexity early.

## Decision
Mirror critical types manually between backend and frontend during Phase 0, using backend schemas and enums as the canonical reference.

## Consequences
Benefits:
- low setup overhead
- fast iteration
- backend remains canonical

Tradeoffs:
- manual mirroring can drift if not maintained carefully
- duplicated type definitions exist temporarily

## Deferred / Follow-up
- generated TypeScript types from OpenAPI
- schema drift checks
- automated contract validation in CI