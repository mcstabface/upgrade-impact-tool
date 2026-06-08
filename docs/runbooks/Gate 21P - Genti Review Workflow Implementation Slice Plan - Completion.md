# Gate 21P — Genti Review Workflow Implementation Slice Plan Completion

## Status

Complete.

## Change Type

Documentation/design only.

No runtime behavior changed.
No runtime test was required.
No generated KBs or runtime artifacts were committed.

## Completed Scope

Gate 21P produced a first-pass implementation slice plan for the Genti review workflow.

Primary artifact:

- `docs/runbooks/Genti Review Workflow Implementation Slice Plan.md`

Checkpoint artifact:

- `docs/runbooks/Gate 21P - Genti Review Workflow Implementation Slice Plan - Checkpoint.md`

## Implementation Slice Defined

The first recommended runtime slice should demonstrate:

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

## Minimum Table Subset Recorded

The plan identifies these first-slice tables:

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

Optional:

- `bug_entry_relationships`

## Minimum Page Subset Recorded

Required first-slice pages:

1. Dashboard
2. Mismatch Review
3. Bug Entry Detail
4. Reports / Exports

Optional first-slice pages:

- Portfolio Upload
- Hierarchy Browser
- Admin / Reference Data

## Runtime Gate Boundary

Gate 21P is complete as docs-only.

The next gate, Gate 21Q, would be runtime/code work.

Gate 21Q must include a pull-and-run script before merge.

## Proposed Gate 21Q

Gate 21Q — Genti Review Workflow Seeded Schema Prototype

Recommended scope:

- add schema DDL or local prototype schema
- add seed data fixture
- add deterministic seed/reset script
- add basic query checks
- do not build full APEX UI yet unless the environment is confirmed

## Proposed Gate 21Q Verification Script

Candidate script:

```bash
scripts/verify_gate_21q_genti_seeded_schema.sh
```

Expected validation:

- at least one portfolio upload exists
- at least eight bug entries exist
- required review statuses exist
- required seed tags exist
- at least one `PDF_ONLY` mismatch exists
- at least one `WEBSITE_ONLY` mismatch exists
- at least one `FIELD_MISMATCH` exists
- at least one bug entry has extracted fields
- at least one bug entry has extracted Bug PDF artifact reference
- status history and audit events can be written for a test action

## Stop Condition

Do not start Gate 21Q unless runtime implementation is explicitly approved or the team accepts a local prototype path.

## Gate 21P Result

Gate 21P is complete and ready to support Gate 21Q planning or stakeholder review.
