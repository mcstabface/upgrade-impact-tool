# Gate 21T — Genti Review Workflow Local Demo CLI Prototype Checkpoint

## Gate

Gate 21T — Genti Review Workflow Local Demo CLI Prototype

## Change Type

Runtime prototype change.

## Branch

`gate-21t-demo-cli`

## Runtime Files Added

- `scripts/genti_demo.sh`
- `scripts/verify_gate_21t_genti_demo_cli.sh`

## Scope

Gate 21T adds a local CLI wrapper around the completed Genti workflow prototype scripts.

The CLI supports:

- preparing the seeded demo database
- checking query/view output
- creating report exports
- printing a compact demo summary
- running the full local demo path

## Verification

Verifier:

```text
scripts/verify_gate_21t_genti_demo_cli.sh
```

The verifier runs the local CLI path and checks summary counts for:

- portfolio uploads
- bug entries
- mismatch flags
- PDF-only mismatches
- Web-site-only mismatches
- field mismatches
- test-required entries
- Bug PDF artifacts
- extracted fields
- audit events
- generated report files

## Expected Summary

```text
Gate 21T demo CLI validation passed
bug_entries: 11
mismatch_flags: 11
test_required_entries: 1
bug_pdf_artifacts: 3
audit_events: 6
report_files_present: 5
```

## Runtime Artifact Policy

The CLI may create or refresh files under:

```text
artifacts/genti_review_workflow/
```

Those are runtime artifacts and should not be committed.

## Boundary

This gate adds a local CLI wrapper only. It does not add production Oracle objects, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

## Current Status

Gate 21T is ready for local pull-and-run verification.
