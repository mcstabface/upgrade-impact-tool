# Gate 21L — Genti Review Workflow Requirements Capture Completion

## Status

Complete.

## Change Type

Documentation-only.

No runtime behavior changed.
No runtime test was required.
No generated KBs or runtime artifacts were committed.

## Completed Scope

Gate 21L records Genti's review workflow requirements before implementation.

The completed requirements capture covers:

1. mismatch flags between the PDF Portfolio and Web-site bug inventories
2. user-controlled review statuses such as `N/A`, `Needs Further Review`, `Test Required`, `Test Deferred`, and `Confirmed`
3. tags per bug entry
4. freeform manual review notes per bug entry
5. hierarchy/navigation such as `MP2 / MP2.1 / Bug 134`
6. storage direction for uploaded portfolios and extracted Bug PDFs
7. Bug detail screen content, including Subsystem, Title, Description, Steps, Screenshots, status, tags, notes, mismatch flags, source portfolio, derived Bug PDF, and audit/history
8. Oracle APEX / Oracle Database hosting direction for the internal Oracle customer

## Decision Recorded

The recommended initial architecture is:

- Oracle APEX for application UI and workflow
- Oracle Database for metadata and workflow state
- Oracle Database tables for status, tags, notes, hierarchy, lineage, and audit
- Oracle Database BLOBs for uploaded portfolios and extracted Bug PDFs in the first internal version
- ORDS where API or web access is needed

Object/document storage remains a future option only if scale, retention, or governance requires it.

## Important Correction Preserved

This is an internal Oracle customer workflow.
It is not Gas South storage.

APEX is therefore a strong fit for the first internal application path.

## Evidence of Completion

Primary artifact:

- `docs/runbooks/Genti Review Workflow Requirements Capture.md`

Checkpoint artifact:

- `docs/runbooks/Gate 21L - Genti Review Workflow Requirements Capture - Checkpoint.md`

## Implementation Guardrail

Do not implement workflow tables, APEX screens, PDF storage mechanics, or mismatch logic until the open workflow and storage questions are resolved or explicitly accepted for a draft/demo slice.

## Next Gate

Gate 21M — Genti Review Workflow Data Model Draft

Gate 21M should be a docs/design gate that drafts the Oracle APEX / Oracle Database relational model for:

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

## Gate 21L Result

Gate 21L is complete and ready to serve as the input for Gate 21M.
