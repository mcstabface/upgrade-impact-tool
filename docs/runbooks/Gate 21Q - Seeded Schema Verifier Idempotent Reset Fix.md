# Gate 21Q — Seeded Schema Verifier Idempotent Reset Fix

## Purpose

Document the fix for the Gate 21Q verifier after local execution on `main` exposed an idempotency issue.

## Problem

Running the verifier against an already-created generated SQLite database failed with:

```text
sqlite3.IntegrityError: FOREIGN KEY constraint failed
```

## Cause

The verifier enabled SQLite foreign key enforcement before dropping tables during reset.

That made the script pass on a fresh database, but fail when re-run against the default generated database path:

```text
artifacts/genti_review_workflow/genti_review_workflow_demo.db
```

## Fix

The verifier now:

1. opens the generated database
2. disables foreign key enforcement only for table teardown
3. drops all known generated tables
4. commits the teardown
5. re-enables foreign key enforcement
6. recreates the schema
7. seeds data
8. validates with foreign key checks enabled

## Verification

The fixed verifier was tested twice against the same database path.

Both runs passed with the expected summary counts.

## Boundary

This fix changes only the local Gate 21Q verifier reset behavior.

It does not add Oracle production schema, APEX pages, PDF extraction, Web-site ingestion, mismatch detection automation, or authorization integration.
