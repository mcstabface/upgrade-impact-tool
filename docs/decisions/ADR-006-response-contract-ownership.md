# ADR-006 — Response Contract Ownership

## Status
Accepted

## Context
Phase 0 required stable response shapes to keep backend and frontend aligned while route shells and workflow surfaces were being built.

## Decision
Backend owns response contract truth.
Frontend conforms to backend response shapes.

## Consequences
Benefits:
- API remains the single operational source of truth
- frontend route shells are forced to align with live responses
- contract drift is easier to detect

Tradeoffs:
- frontend convenience models must mirror backend intentionally
- changes to backend response shape require coordinated frontend updates

## Deferred / Follow-up
- automated schema export
- generated frontend clients
- contract tests between frontend and backend