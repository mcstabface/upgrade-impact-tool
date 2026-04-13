# ADR-003 — Migration Tool Choice

## Status
Accepted

## Context
Phase 0 required deterministic schema setup, repeatable migration application, and clear versioned database evolution.

## Decision
Use Alembic for schema migrations with PostgreSQL as the database engine.

## Consequences
Benefits:
- versioned migration history
- repeatable local environment setup
- controlled schema evolution
- explicit upgrade/downgrade structure

Tradeoffs:
- migrations must be maintained carefully by hand
- schema drift can still happen if ad hoc SQL is introduced outside migration files

## Deferred / Follow-up
- no automated migration testing harness in Phase 0
- no production deployment migration process in Phase 0