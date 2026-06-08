# Gate 21M — Genti Review Workflow Data Model Draft Checkpoint

## Gate

Gate 21M — Genti Review Workflow Data Model Draft

## Change Type

Documentation-only checkpoint.

No runtime code was changed.
No generated knowledge bases or runtime artifacts are committed.
No runtime test is required for this gate.

## Primary Draft Artifact

- `docs/runbooks/Genti Review Workflow Data Model Draft.md`

## Input Artifact

- `docs/runbooks/Genti Review Workflow Requirements Capture.md`

## Scope Captured

The data model draft maps Genti's requirements into an Oracle APEX / Oracle Database relational design for:

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
- `bug_entry_relationships`
- `bug_pdf_artifacts`
- `bug_extracted_fields`
- `audit_events`

## Architecture Direction Preserved

The draft preserves the Gate 21L architecture direction:

- Oracle APEX for application UI and workflow
- Oracle Database for metadata and workflow state
- Oracle Database tables for status, tags, notes, hierarchy, lineage, and audit
- Oracle Database BLOBs for uploaded portfolios and extracted Bug PDFs in the first internal version
- approved Oracle object/document storage as a future alternative if scale, retention, or governance requires it

## Boundary

This checkpoint does not implement:

- schema DDL
- migrations
- APEX pages
- PDF storage mechanics
- extraction logic
- mismatch detection logic
- workflow mutation behavior

## Current Status

The Gate 21M relational model draft has been added and is ready for review.

## Next Step

Complete Gate 21M with a docs-only completion artifact, then proceed to the next design gate.
