# Genti Review Workflow Demo Handoff Summary

## Gate

Gate 21W — Genti Review Workflow Demo Handoff Summary

## Purpose

Provide a concise handoff summary for the local Genti review workflow demo state after Gates 21L through 21V.

This document is intended for demo preparation, stakeholder alignment, and next-step planning.

## Current Demo Status

The local deterministic demo path is ready.

It supports:

- seeded Genti review workflow database
- PDF Portfolio and Web-site inventory representation
- canonical bug entries
- mismatch flags
- status, tag, note, and audit workflow rows
- extracted Bug PDF metadata
- deterministic query/view validation
- deterministic report exports
- local CLI wrapper
- compact summary mode
- generated file listing
- cleanup command

## Completed Gates

| Gate | Result |
|---|---|
| Gate 21L | Requirements capture completed. |
| Gate 21M | Oracle APEX / Oracle Database data model draft completed. |
| Gate 21N | APEX page-flow draft completed. |
| Gate 21O | Demo script draft completed. |
| Gate 21P | Implementation slice plan completed. |
| Gate 21Q | Seeded schema prototype completed and merged. |
| Gate 21R | Query/view prototype completed and merged. |
| Gate 21S | Report export prototype completed and merged. |
| Gate 21T | Local demo CLI prototype completed and merged. |
| Gate 21U | Demo readiness packet completed and merged. |
| Gate 21V | Local demo CLI polish completed and merged. |

## Main Demo Command

From repo root:

```bash
bash scripts/genti_demo.sh quiet
```

This runs the full local demo path and prints only the compact summary.

## Full Verbose Demo Command

```bash
bash scripts/genti_demo.sh all
```

This runs the full local demo path with the underlying verifier output included.

## Stage-by-Stage Commands

```bash
bash scripts/genti_demo.sh prepare
bash scripts/genti_demo.sh query
bash scripts/genti_demo.sh reports
bash scripts/genti_demo.sh summary
bash scripts/genti_demo.sh show-files
```

## Cleanup Command

```bash
bash scripts/genti_demo.sh clean
```

This removes generated local demo artifacts under:

```text
artifacts/genti_review_workflow/
```

## Verification Commands

Current verification entry points:

```bash
bash scripts/verify_gate_21q_genti_seeded_schema.sh
bash scripts/verify_gate_21r_genti_query_views.sh
bash scripts/verify_gate_21s_genti_report_exports.sh
bash scripts/verify_gate_21t_genti_demo_cli.sh
bash scripts/verify_gate_21u_genti_demo_readiness.sh
bash scripts/verify_gate_21v_genti_demo_polish.sh
```

Recommended pre-demo verification:

```bash
bash scripts/verify_gate_21v_genti_demo_polish.sh
```

## Expected Demo Summary

The compact demo summary should include:

```text
bug_entries: 11
mismatch_flags: 11
test_required_entries: 1
bug_pdf_artifacts: 3
audit_events: 6
report_files_present: 5
```

## Generated Runtime Artifacts

The demo may create or refresh:

```text
artifacts/genti_review_workflow/genti_review_workflow_demo.db
artifacts/genti_review_workflow/reports/genti_mismatch_review.csv
artifacts/genti_review_workflow/reports/genti_test_required.csv
artifacts/genti_review_workflow/reports/genti_bug_136_detail.json
artifacts/genti_review_workflow/reports/genti_audit_history.csv
artifacts/genti_review_workflow/reports/genti_mismatch_review.md
```

These generated files are runtime artifacts and must not be committed.

## Demo Narrative

Use this framing:

The local demo shows the proposed Genti review workflow data path before building Oracle APEX pages. It starts with a deterministic seeded workflow database, then demonstrates mismatch review, Bug Entry Detail data, status/tag/note workflow state, audit history, and exportable reports.

This is not the production Oracle APEX application. It is the verified local substrate for the APEX demo.

## What to Show

Recommended sequence:

1. Run `bash scripts/genti_demo.sh quiet`.
2. Run `bash scripts/genti_demo.sh show-files`.
3. Open `artifacts/genti_review_workflow/reports/genti_mismatch_review.csv`.
4. Open `artifacts/genti_review_workflow/reports/genti_test_required.csv`.
5. Open `artifacts/genti_review_workflow/reports/genti_bug_136_detail.json`.
6. Open `artifacts/genti_review_workflow/reports/genti_audit_history.csv`.
7. Explain that these are generated report outputs from the seeded workflow database.

## Open Decisions for Genti

Confirm before APEX implementation:

1. Are the mismatch categories sufficient for the first APEX demo?
2. Which fields must be compared between PDF Portfolio and Web-site sources?
3. Should extracted fields remain read-only?
4. Are the seeded statuses sufficient for first workflow review?
5. Should tags be controlled, freeform, or admin-managed?
6. Are notes editable, append-only, or versioned?
7. Is link/download sufficient for extracted Bug PDFs, or is inline preview required?
8. Is Oracle Database BLOB storage acceptable for the first internal version?
9. Which report is highest priority for the first APEX screen/export?
10. What Oracle authentication and authorization model should be used?

## Recommended Next Gate

Gate 21X — Genti Review Workflow APEX Implementation Decision Record

Recommended scope:

- capture Genti decisions from demo review
- decide whether to proceed to APEX build, local prototype refinement, or data-model adjustment
- record APEX environment assumptions
- record storage decision
- record first implementation slice acceptance criteria

## Boundary

This handoff summary does not add production Oracle objects, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

It summarizes the current local deterministic demo state and next decision points.
