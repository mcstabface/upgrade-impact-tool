# Gate 21M — Genti Review Workflow Data Model Draft Completion

## Status

Complete.

## Change Type

Documentation/design only.

No runtime behavior changed.
No runtime test was required.
No generated KBs or runtime artifacts were committed.

## Completed Scope

Gate 21M produced a first-pass Oracle APEX / Oracle Database relational model for Genti's review workflow.

Primary artifact:

- `docs/runbooks/Genti Review Workflow Data Model Draft.md`

Checkpoint artifact:

- `docs/runbooks/Gate 21M - Genti Review Workflow Data Model Draft - Checkpoint.md`

## Tables Drafted

The model covers:

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

## Design Direction Recorded

The data model draft records:

- immutable uploaded portfolio source artifacts
- derived extracted Bug PDF artifacts
- separate PDF Portfolio and Web-site inventory tables
- canonical APEX-facing `bug_entries`
- structured mismatch flags with raw compared values
- configurable review statuses
- status history
- controlled tag dictionary plus entry tag assignments
- freeform manual notes
- maintenance-pack hierarchy
- optional bug relationships/cross-links
- extracted Bug PDF BLOB storage and lineage
- flexible extracted-field storage for Subsystem, Title, Description, Steps, Screenshots, and future fields
- append-only audit events

## Architecture Guardrails Preserved

The draft preserves the internal Oracle direction:

- Oracle APEX for UI/workflow
- Oracle Database for workflow truth
- Oracle DB BLOBs for first-version uploaded portfolios and extracted Bug PDFs
- external Oracle object/document storage only as a future option if scale/governance requires it

The draft also preserves the non-implementation boundary:

- no schema DDL
- no migrations
- no runtime pipeline change
- no APEX page implementation
- no mismatch detection implementation
- no PDF extraction/storage implementation

## Open Questions Remaining

The following remain intentionally open before implementation:

1. Are status values fixed, admin-configurable, or both?
2. Are tags controlled vocabulary, freeform, or admin-managed controlled vocabulary?
3. Are notes editable, append-only, or versioned?
4. Can a bug belong to multiple maintenance packs?
5. Are bug relationships strictly hierarchical, or can they include cross-links?
6. Should extracted fields be user-editable, or only reviewable with annotations?
7. Should mismatch flags be system-generated only, user-editable, or system-generated with user disposition?
8. Is Oracle DB BLOB storage acceptable for the first internal version?
9. What are expected volume, retention, and backup requirements?
10. What APEX authentication/authorization model should be used?

## Next Gate

Recommended next gate:

Gate 21N — Genti Review Workflow APEX Page Flow Draft

Recommended scope:

- Dashboard page layout
- Portfolio upload page
- Mismatch review report
- Hierarchy browser
- Bug entry detail page
- Reports/export page
- role assumptions and navigation flow

## Gate 21M Result

Gate 21M is complete and ready to serve as the design input for Gate 21N.
