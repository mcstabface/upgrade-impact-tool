# Gate 21N — Genti Review Workflow APEX Page Flow Draft Completion

## Status

Complete.

## Change Type

Documentation/design only.

No runtime behavior changed.
No runtime test was required.
No generated KBs or runtime artifacts were committed.

## Completed Scope

Gate 21N produced a first-pass Oracle APEX page-flow draft for the Genti review workflow.

Primary artifact:

- `docs/runbooks/Genti Review Workflow APEX Page Flow Draft.md`

Checkpoint artifact:

- `docs/runbooks/Gate 21N - Genti Review Workflow APEX Page Flow Draft - Checkpoint.md`

## Pages Drafted

The page-flow draft covers:

- Dashboard
- Portfolio Upload
- Mismatch Review
- Hierarchy Browser
- Bug Entry Detail
- Reports / Exports
- optional Admin / Reference Data

## Demo Flow Recorded

The first recommended demo sequence is:

1. Open Dashboard.
2. Show total entries, mismatch counts, and status counts.
3. Open Mismatch Review.
4. Filter to `FIELD_MISMATCH` or `PDF_ONLY`.
5. Open a Bug Entry Detail.
6. Show extracted Subsystem, Title, Description, Steps, and Screenshots.
7. Show extracted Bug PDF link or preview.
8. Set status to `Test Required`.
9. Add a tag such as `Needs Validation`.
10. Add a manual note.
11. Show audit/history updated.
12. Return to Dashboard and show changed status count.
13. Open Reports / Exports and show filtered review report.

## APEX Design Direction Recorded

The draft records:

- dashboard summary cards
- portfolio upload visibility
- mismatch queue with side-by-side PDF Portfolio and Web-site values
- maintenance-pack hierarchy navigation
- bug detail review page
- status, tag, and note workflow sections
- extracted Bug PDF link/download or preview
- audit/history panel
- report/export entry points
- initial role assumptions for Viewer, Reviewer, and Admin

## Non-Implementation Boundary Preserved

Gate 21N did not create:

- APEX pages
- database schema
- migrations
- processing jobs
- PDF extraction logic
- mismatch detection logic
- authorization integration

## Open Questions Remaining

The following remain open before implementation:

1. Which Oracle/internal authentication model will be used?
2. Are roles mapped from Oracle groups?
3. Can all reviewers see all maintenance packs?
4. Who can upload portfolios?
5. Who can change status values or tags?
6. Who can export reports?
7. Should extracted Bug PDFs be embedded inline or opened separately?
8. Are tags and statuses configurable in the first demo, or seeded only?

## Next Gate

Recommended next gate:

Gate 21O — Genti Review Workflow Demo Script Draft

Recommended scope:

- live demo sequence
- demo data assumptions
- talking points
- page-by-page script
- expected user questions
- implementation blockers to clarify with Genti

## Gate 21N Result

Gate 21N is complete and ready to serve as the design input for Gate 21O.
