# Genti Review Workflow Implementation Slice Plan

## Gate

Gate 21P — Genti Review Workflow Implementation Slice Plan

## Purpose

Define the smallest implementable demo slice for the Genti review workflow after the requirements, data model, APEX page flow, and demo script drafts.

This plan is the bridge between design documentation and the first runtime implementation gate.

## Change Type

Documentation/design only.

No runtime behavior changes are included in this gate.
No schema, migration, APEX page, extraction, or workflow implementation is included in this gate.
No generated KBs or runtime artifacts should be committed for this gate.
No runtime test is required.

## Design Inputs

- `docs/runbooks/Genti Review Workflow Requirements Capture.md`
- `docs/runbooks/Genti Review Workflow Data Model Draft.md`
- `docs/runbooks/Genti Review Workflow APEX Page Flow Draft.md`
- `docs/runbooks/Genti Review Workflow Demo Script Draft.md`

## Implementation Goal

Build the minimum vertical slice needed to demonstrate:

1. a portfolio exists as a source artifact
2. PDF Portfolio bug inventory and Web-site bug inventory are represented separately
3. canonical bug entries link the two source inventories
4. mismatch flags are visible
5. reviewers can inspect a bug detail view
6. reviewers can change status
7. reviewers can assign a tag
8. reviewers can add a manual note
9. an extracted Bug PDF artifact is linked
10. audit/history records workflow actions

## Explicit Non-Goals for First Slice

Do not implement the full future application in the first slice.

Defer:

- full ingestion automation from uploaded PDF Portfolio
- full Web-site crawling/import automation
- full PDF extraction pipeline integration
- embedded PDF viewer if the environment complicates it
- complex role/permission model
- admin screens for every reference table
- bulk edit workflows
- advanced report formatting
- production retention/backup controls
- external object/document storage integration

## First Slice Architecture

The first runtime slice should be a seeded/demo workflow over a small curated dataset.

Recommended shape:

```text
Seed/demo data
  ↓
Oracle-style relational tables or local equivalent during prototype
  ↓
APEX/demo pages
  ↓
Workflow actions: status, tag, note
  ↓
Audit events
```

## Minimum Table Subset

### Required for first demo

- `portfolio_uploads`
- `portfolio_bug_inventory`
- `website_bug_inventory`
- `bug_entries`
- `mismatch_flags`
- `review_statuses`
- `bug_entry_status_history`
- `tag_dictionary`
- `bug_entry_tags`
- `bug_entry_notes`
- `maintenance_packs`
- `bug_pdf_artifacts`
- `bug_extracted_fields`
- `audit_events`

### Optional for first demo

- `bug_entry_relationships`

Use `bug_entry_relationships` only if the first demo must show multiple maintenance-pack membership or cross-links.

If hierarchy is strict for the demo, `bug_entries.maintenance_pack_id` is enough.

## Minimum Page Subset

### Required pages

1. Dashboard
2. Mismatch Review
3. Bug Entry Detail
4. Reports / Exports

### Optional pages

5. Portfolio Upload
6. Hierarchy Browser
7. Admin / Reference Data

### Rationale

The first demo can prove workflow value with Dashboard → Mismatch Review → Bug Detail → Reports.

Portfolio Upload and Hierarchy Browser are useful but can be represented as read-only/seeded views if implementation time is constrained.

## Minimum Workflow Actions

The first runtime slice should support these user-visible actions:

1. view mismatch list
2. open bug detail
3. change bug review status
4. add tag to bug entry
5. add manual note
6. view extracted Bug PDF link/download reference
7. view audit/history for actions taken

Do not implement bulk updates in the first slice.

## Seed Data Requirements

Use a curated dataset with enough variety to prove the workflow without noise.

Suggested seed shape:

| Seed Item | Count | Purpose |
|---|---:|---|
| Portfolio upload | 1 | Source artifact anchor. |
| Maintenance packs | 2–3 | Hierarchy/context. |
| Bug entries | 8–12 | Enough for filtering and navigation. |
| PDF-only mismatches | 1–2 | Show missing Web-site match. |
| Web-site-only mismatches | 1–2 | Show missing PDF match. |
| Field mismatches | 2–3 | Show side-by-side comparison. |
| Matched entries | 1–2 | Show normal case. |
| Extracted Bug PDF artifacts | 2–3 | Show derived PDF evidence. |
| Extracted fields per demo bug | 4–5 | Subsystem, Title, Description, Steps, Screenshots. |
| Tags | 3–5 | Filtering/grouping. |
| Manual notes | 1–2 initial notes | Demonstrate notes panel. |

## Seed Review Statuses

Required seed statuses:

- `New`
- `Needs Further Review`
- `Test Required`
- `Test Deferred`
- `Confirmed`
- `N/A`
- `Blocked`
- `Resolved`

## Seed Tags

Recommended seed tags:

- `Needs Validation`
- `Regression Risk`
- `Customer Visible`
- `Testing Candidate`
- `Documentation Check`

## Suggested First Runtime Gate After 21P

Gate 21Q — Genti Review Workflow Seeded Schema Prototype

Recommended scope:

- add schema DDL or local prototype schema
- add seed data fixture
- add deterministic seed/reset script
- add basic query checks
- do not build full APEX UI yet unless the environment is confirmed

## Runtime Work Requirements Starting at 21Q

Because Gate 21Q would be runtime/code work, it must include a pull-and-run script before merge.

The script should:

1. create or reset the demo database/schema
2. load seed data
3. run validation queries
4. print counts and expected sample rows
5. exit non-zero on validation failure

## Proposed Pull-and-Run Script Shape for Runtime Gate

Candidate script name:

```bash
scripts/verify_gate_21q_genti_seeded_schema.sh
```

Expected behavior:

```bash
#!/usr/bin/env bash
set -euo pipefail

# create/reset demo schema or local equivalent
# load seed data
# run validation checks
# print summary counts
```

Expected validation checks:

- at least one portfolio upload exists
- at least eight bug entries exist
- required review statuses exist
- required seed tags exist
- at least one `PDF_ONLY` mismatch exists
- at least one `WEBSITE_ONLY` mismatch exists
- at least one `FIELD_MISMATCH` exists
- at least one bug entry has extracted fields
- at least one bug entry has an extracted Bug PDF artifact reference
- status history and audit events can be written for a test action

## Acceptance Criteria for First Runtime Slice

A first runtime slice is acceptable when:

1. seed/reset is deterministic
2. required tables exist
3. seed data loads cleanly
4. required statuses and tags are present
5. mismatch records are queryable
6. bug detail data can be queried from the canonical bug entry
7. status update creates status history
8. tag assignment creates tag row
9. note creation creates note row
10. each workflow action creates an audit event
11. extracted Bug PDF artifact metadata is queryable
12. validation script exits successfully

## APEX Implementation Readiness Criteria

Before actual APEX page build, confirm:

1. target APEX workspace/environment
2. schema ownership
3. authentication model
4. authorization role model
5. BLOB storage approval
6. PDF preview approach
7. first report/export requirements
8. who will own seed/demo data

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| APEX environment not confirmed | Blocks UI implementation | Start with seeded schema and query validation. |
| BLOB storage decision unresolved | Blocks final storage implementation | Use metadata/link placeholder until confirmed. |
| Status/tag governance unresolved | Causes rework | Seed controlled statuses/tags and keep admin config deferred. |
| Extracted field editability unresolved | Causes data model change | Keep extracted fields read-only and store notes separately. |
| Hierarchy multiplicity unresolved | Can affect relationships | Keep `bug_entry_relationships` optional until confirmed. |
| PDF preview behavior unresolved | Can slow demo | Use link/download first. |

## Proposed Implementation Order After Approval

1. Seeded schema prototype
2. Seed/reset validation script
3. query/report views for dashboard and mismatch list
4. workflow action functions for status/tag/note
5. audit event writes
6. Bug Entry Detail query shape
7. report/export query shape
8. APEX page build or local UI prototype, depending on environment availability

## Stop Conditions

Do not start runtime implementation until at least one of the following is true:

1. Genti approves this slice as the first demo target.
2. The team explicitly accepts the open assumptions for a prototype.
3. APEX environment details are provided.
4. A local prototype is explicitly requested as an interim demo path.

## Next Gate

Gate 21Q — Genti Review Workflow Seeded Schema Prototype

This next gate would be runtime/code work and must include a pull-and-run script before merge.
