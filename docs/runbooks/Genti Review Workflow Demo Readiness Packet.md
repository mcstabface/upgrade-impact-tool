# Genti Review Workflow Demo Readiness Packet

## Gate

Gate 21U — Genti Review Workflow Demo Readiness Packet

## Purpose

Provide an operator-ready packet for running and explaining the local Genti review workflow demo.

This packet uses the completed local prototype gates:

- Gate 21Q — seeded schema prototype
- Gate 21R — query/view prototype
- Gate 21S — report export prototype
- Gate 21T — local demo CLI prototype

## Demo Goal

Show a deterministic local workflow that represents the proposed Oracle APEX / Oracle Database review application before building APEX pages.

The local demo proves:

1. a seeded portfolio source exists
2. PDF Portfolio and Web-site bug inventories are represented separately
3. canonical bug entries link source inventory records
4. mismatch flags are queryable
5. Bug Entry Detail data is available for review
6. status, tag, note, and audit rows exist
7. extracted Bug PDF metadata is represented
8. deterministic reports can be generated

## Pre-Demo Setup

From repo root:

```bash
cd /home/stabby/Documents/upgrade-impact-tool

git checkout main
git fetch origin
git pull --ff-only origin main
```

## Primary Demo Command

Run the full local demo path:

```bash
bash scripts/genti_demo.sh all
```

This command prepares the demo database, validates query views, generates reports, and prints a compact summary.

## Individual Demo Commands

Use these commands when showing each stage separately:

```bash
bash scripts/genti_demo.sh prepare
bash scripts/genti_demo.sh query
bash scripts/genti_demo.sh reports
bash scripts/genti_demo.sh summary
```

## Verification Command

Use the Gate 21T verifier before demo:

```bash
bash scripts/verify_gate_21t_genti_demo_cli.sh
```

Expected summary:

```text
Gate 21T demo CLI validation passed
bug_entries: 11
mismatch_flags: 11
test_required_entries: 1
bug_pdf_artifacts: 3
audit_events: 6
report_files_present: 5
```

## Generated Runtime Artifacts

The local demo creates runtime artifacts under:

```text
artifacts/genti_review_workflow/
```

Generated database:

```text
artifacts/genti_review_workflow/genti_review_workflow_demo.db
```

Generated reports:

```text
artifacts/genti_review_workflow/reports/genti_mismatch_review.csv
artifacts/genti_review_workflow/reports/genti_test_required.csv
artifacts/genti_review_workflow/reports/genti_bug_136_detail.json
artifacts/genti_review_workflow/reports/genti_audit_history.csv
artifacts/genti_review_workflow/reports/genti_mismatch_review.md
```

These generated files must not be committed.

## Suggested Demo Flow

### 1. Start with the summary

Command:

```bash
bash scripts/genti_demo.sh summary
```

Talking point:

The local demo has a seeded portfolio, 11 canonical bug entries, 11 mismatch flags, and five generated report files. The point is to show the proposed review workflow data shape before APEX UI buildout.

### 2. Show the seeded schema validation

Command:

```bash
bash scripts/genti_demo.sh prepare
```

Talking point:

The seeded schema proves that portfolio upload, PDF inventory, Web-site inventory, canonical bug entries, mismatch flags, statuses, tags, notes, extracted Bug PDF metadata, and audit events are all represented.

### 3. Show the query/view validation

Command:

```bash
bash scripts/genti_demo.sh query
```

Talking point:

The query/view layer proves that dashboard, mismatch review, Bug Entry Detail, workflow history, and audit data can be read deterministically from the seeded schema.

### 4. Show the report generation

Command:

```bash
bash scripts/genti_demo.sh reports
```

Talking point:

The report export layer proves that the same data can produce review outputs such as mismatch review, test-required entries, selected bug detail, and audit history.

### 5. Inspect generated files

Suggested files to inspect:

```text
artifacts/genti_review_workflow/reports/genti_mismatch_review.csv
artifacts/genti_review_workflow/reports/genti_test_required.csv
artifacts/genti_review_workflow/reports/genti_bug_136_detail.json
artifacts/genti_review_workflow/reports/genti_audit_history.csv
artifacts/genti_review_workflow/reports/genti_mismatch_review.md
```

Talking point:

These files are demo outputs. They show what the future APEX pages and report exports would be reading from the database.

## Demo Narrative

Recommended opening:

This local demo shows the proposed Genti review workflow data path before building the Oracle APEX UI. It starts with a seeded source portfolio and Web-site inventory, then shows canonical bug entries, mismatch flags, status/tag/note workflow data, extracted Bug PDF metadata, audit history, and deterministic report exports.

Recommended close:

This is not the final APEX application. It is the verified local workflow substrate for the APEX demo: data shape, query shape, reports, and operator commands are now deterministic.

## Questions to Ask Genti

1. Are the mismatch categories sufficient for the first APEX demo?
2. Should extracted fields remain read-only?
3. Are `Test Required`, `Test Deferred`, `Confirmed`, `N/A`, and `Needs Further Review` enough for the first workflow?
4. Should tags be controlled or freeform?
5. Is link/download sufficient for extracted Bug PDFs, or is inline preview required?
6. Which report is highest priority: mismatch review, test-required, bug detail, or audit history?
7. Is Oracle DB BLOB storage acceptable for the first internal version?

## Cleanup

To remove generated local demo artifacts:

```bash
rm -rf artifacts/genti_review_workflow/
```

Recreate them with:

```bash
bash scripts/genti_demo.sh all
```

## Runtime Artifact Policy

Generated files under `artifacts/genti_review_workflow/` are runtime artifacts.

Do not commit:

- generated SQLite database files
- generated CSV reports
- generated JSON reports
- generated Markdown reports

## Boundary

This readiness packet does not add Oracle production schema, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

It documents how to run and explain the local deterministic demo path.

## Next Gate Candidate

Gate 21V — Genti Review Workflow Local Demo Polish

Possible scope:

- reduce noisy output from `genti_demo.sh all`
- add a quiet mode
- add a `show-files` command
- add a `clean` command
- improve local operator ergonomics without changing data model behavior
