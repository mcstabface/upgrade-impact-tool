# Gate 21S — Genti Review Workflow Report Export Prototype Checkpoint

## Gate

Gate 21S — Genti Review Workflow Report Export Prototype

## Change Type

Runtime prototype change.

## Branch

`gate-21s-report-exports`

## Runtime File Added

- `scripts/verify_gate_21s_genti_report_exports.sh`

## Scope

Gate 21S adds deterministic report/export validation over the Gate 21Q seeded SQLite database.

The verifier first runs the Gate 21Q seed verifier. It then writes generated report files under:

```text
artifacts/genti_review_workflow/reports/
```

Those report files are runtime artifacts and should not be committed.

## Generated Reports

- `genti_mismatch_review.csv`
- `genti_test_required.csv`
- `genti_bug_136_detail.json`
- `genti_audit_history.csv`
- `genti_mismatch_review.md`

## Validation Coverage

The verifier checks:

- all expected report files exist
- all expected report files are non-empty
- mismatch export has seven rows
- mismatch export includes `BUG-136` as a `FIELD_MISMATCH`
- test-required export contains `BUG-136`
- bug detail export is for `BUG-136`
- bug detail export has `TEST_REQUIRED` status
- bug detail export includes extracted fields, Bug PDF metadata, tags, and notes
- audit export has six rows
- audit export includes `STATUS_CHANGED`
- Markdown report contains expected title and bug identifier

## Verification Command

From repo root:

```bash
bash scripts/verify_gate_21s_genti_report_exports.sh
```

Optional custom paths:

```bash
bash scripts/verify_gate_21s_genti_report_exports.sh /tmp/genti_review_workflow_demo.db /tmp/genti_reports
```

## Expected Summary

```text
Gate 21S report/export validation passed
export_dir: artifacts/genti_review_workflow/reports
mismatch_export_rows: 7
test_required_export_rows: 1
bug_detail_export_id: BUG-136
bug_detail_export_fields: 4
audit_export_rows: 6
export_files: 5
```

## Boundary

This gate adds generated report validation only. It does not add production Oracle objects, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

## Current Status

Gate 21S is ready for local pull-and-run verification.
