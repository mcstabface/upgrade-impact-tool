# Gate 21R — Genti Review Workflow Query View Prototype Checkpoint

## Gate

Gate 21R — Genti Review Workflow Query View Prototype

## Change Type

Runtime prototype change.

## Branch

`gate-21r-query-views`

## Runtime File Added

- `scripts/verify_gate_21r_genti_query_views.sh`

## Scope

Gate 21R adds deterministic read-side checks over the Gate 21Q seeded SQLite database.

The verifier first runs the Gate 21Q seed verifier. It then builds temporary JSON output and checks that the expected read-side views are present.

## Covered Views

- dashboard summary
- mismatch review list
- bug detail for `BUG-136`
- extracted fields
- extracted Bug PDF metadata
- active tags
- manual notes
- status history
- audit rows

## Verification Command

From repo root:

```bash
bash scripts/verify_gate_21r_genti_query_views.sh
```

Optional custom database path:

```bash
bash scripts/verify_gate_21r_genti_query_views.sh /tmp/genti_review_workflow_demo.db
```

## Expected Summary

```text
Gate 21R query/view validation passed
dashboard_bug_entries: 11
dashboard_mismatch_flags: 11
mismatch_review_rows: 7
bug_detail_id: BUG-136
bug_detail_status: TEST_REQUIRED
bug_detail_extracted_fields: 4
bug_detail_pdf_artifacts: 1
workflow_status_history_rows: 1
workflow_active_tag_rows: 1
workflow_note_rows: 2
workflow_audit_event_rows: 4
```

## Boundary

This gate adds read-side prototype validation only. It does not add production Oracle objects, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

## Current Status

Gate 21R is ready for local pull-and-run verification.
