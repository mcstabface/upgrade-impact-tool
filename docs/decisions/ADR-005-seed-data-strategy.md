# ADR-004 — Phase 0 Authentication Approach

## Status
Accepted

## Context
Phase 0 is focused on skeleton validation, deterministic workflow behavior, API contract alignment, and frontend route proof. Full authentication and authorization would add complexity without materially improving Phase 0 validation.

## Decision
Do not implement full authentication in Phase 0.
Assume trusted local development use only.

## Consequences
Benefits:
- faster validation of the product skeleton
- less infrastructure overhead
- focus remains on intake, workflow, results, and evidence surfaces

Tradeoffs:
- no real user identity enforcement
- user_id fields written in audit paths are placeholders
- permissions model remains documented but not enforced

## Deferred / Follow-up
- role-based access control
- real user identity propagation
- admin-only route protection
- audit attribution to authenticated users