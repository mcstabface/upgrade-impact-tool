# Gate 21L — Genti Review Workflow Requirements Capture Checkpoint

## Gate

Gate 21L — Genti Review Workflow Requirements Capture

## Change Type

Documentation-only checkpoint.

No runtime code was changed.
No generated knowledge bases or runtime artifacts are committed.
No runtime test is required for this gate.

## Source Requirement Artifact

Primary requirements capture:

- `docs/runbooks/Genti Review Workflow Requirements Capture.md`

## Verified Current State

The Genti workflow requirements capture document is present on `main`.

It records the current customer feedback scope for:

- PDF Portfolio versus Web-site bug mismatch flags
- entry-level review statuses
- tags per entry
- freeform manual review notes
- maintenance-pack and bug hierarchy navigation
- extracted Bug PDF storage
- Bug PDF component display
- Oracle APEX hosting and Oracle Database storage direction

## Validated Actual Corpus / Demo Baseline

The requirements capture records the actual corpus/demo baseline as:

| Metric | Value |
|---|---:|
| Actual corpus files | 25 |
| HTML source files | 4 |
| Portfolio PDFs | 21 |
| KB documents | 4 |
| Search-context artifacts | 179 |
| Extraction failures | 0 |
| Empty text artifacts | 0 |
| Extracted characters | 1,479,153 |
| Extracted pages | 1,353 |
| Demo candidate count | 10 |

## Architecture Direction Captured

The captured recommendation is Oracle-native:

- Oracle APEX for UI and workflow
- Oracle Database for metadata, review status, tags, notes, hierarchy, lineage, and audit
- Oracle Database BLOB storage for uploaded portfolios and extracted Bug PDFs in the first version
- Approved Oracle document/object storage as a future alternative only if scale, retention, or governance requires it

## Gate Boundary

This gate captures requirements only.

It does not implement:

- workflow tables
- APEX screens
- mismatch detection logic
- PDF extraction/storage changes
- status/tag/note mutation behavior

## Stop Condition Preserved

Implementation remains blocked until the following are confirmed:

- status values
- tag model
- note behavior
- hierarchy rules
- PDF storage choice
- APEX environment
- Bug detail screen fields

## Next Gate

Gate 21M — Genti Review Workflow Data Model Draft

Gate 21M should remain docs/design first and draft the Oracle APEX / Oracle Database relational model before runtime implementation.
