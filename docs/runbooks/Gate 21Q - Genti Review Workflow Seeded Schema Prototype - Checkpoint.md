# Gate 21Q — Genti Review Workflow Seeded Schema Prototype Checkpoint

## Gate

Gate 21Q — Genti Review Workflow Seeded Schema Prototype

## Change Type

Runtime/prototype change.

This gate adds a local SQLite seeded schema verification path for the Genti review workflow.

## Branch

`gate-21q-genti-seeded-schema`

## Runtime Files Added

- `scripts/verify_gate_21q_genti_seeded_schema.sh`

## Scope Implemented

The verifier script creates a deterministic local SQLite prototype database under:

```text
artifacts/genti_review_workflow/genti_review_workflow_demo.db
```

The generated database is a runtime artifact and should not be committed.

The script creates and validates seeded data for:

- portfolio upload source artifact
- maintenance-pack hierarchy
- PDF Portfolio bug inventory
- Web-site bug inventory
- canonical bug entries
- mismatch flags
- review statuses
- tag dictionary
- status history
- tag assignment
- manual notes
- extracted Bug PDF artifact references
- extracted fields
- audit events

## Verification Command

From repo root:

```bash
bash scripts/verify_gate_21q_genti_seeded_schema.sh
```

Optional custom database path:

```bash
bash scripts/verify_gate_21q_genti_seeded_schema.sh /tmp/genti_review_workflow_demo.db
```

## Local Verification Result

The verifier was tested locally before pushing.

Observed output summary:

```text
Gate 21Q seeded schema validation passed
audit_events: 6
bug_entries: 11
bug_extracted_fields: 10
bug_pdf_artifacts: 3
field_mismatches: 2
maintenance_packs: 3
mismatch_flags: 11
note_rows: 2
pdf_only_mismatches: 3
portfolio_uploads: 1
review_statuses: 8
schema_version: genti_review_workflow_seeded_schema_v1
status_history_rows: 1
tag_assignment_rows: 1
tags: 5
website_only_mismatches: 2
```

## Validation Coverage

The script exits non-zero if any required condition fails.

It validates:

- at least one portfolio upload exists
- at least eight bug entries exist
- required review statuses exist
- required seed tags exist
- at least one `PDF_ONLY` mismatch exists
- at least one `WEBSITE_ONLY` mismatch exists
- at least one `FIELD_MISMATCH` exists
- at least one bug entry has extracted fields
- at least one bug entry has an extracted Bug PDF artifact reference
- status history can be written
- tag assignment can be written
- manual notes can be written
- audit events can be written for status, tag, and note actions

## Boundary

This gate does not implement:

- Oracle production schema
- APEX pages
- PDF extraction
- Web-site ingestion
- mismatch detection automation
- authorization integration

## Current Status

Gate 21Q implementation is ready for PR review.
