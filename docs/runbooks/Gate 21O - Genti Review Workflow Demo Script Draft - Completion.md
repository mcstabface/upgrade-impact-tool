# Gate 21O — Genti Review Workflow Demo Script Draft Completion

## Status

Complete.

## Change Type

Documentation/design only.

No runtime behavior changed.
No runtime test was required.
No generated KBs or runtime artifacts were committed.

## Completed Scope

Gate 21O produced a first-pass stakeholder-facing demo script for the Genti review workflow.

Primary artifact:

- `docs/runbooks/Genti Review Workflow Demo Script Draft.md`

Checkpoint artifact:

- `docs/runbooks/Gate 21O - Genti Review Workflow Demo Script Draft - Checkpoint.md`

## Demo Script Coverage

The demo script records:

- demo objective
- opening message
- key positioning
- demo data assumptions
- seed review statuses
- seed tags
- page-by-page demo actions
- talking points
- expected reactions
- questions to ask Genti
- expected user questions and recommended answers
- implementation blockers to clarify
- recommended first implementation slice after approval

## Live Demo Sequence Recorded

The script follows this sequence:

1. Dashboard
2. Portfolio Upload view
3. Mismatch Review queue
4. Field mismatch example
5. Hierarchy Browser
6. Bug Entry Detail
7. Status update
8. Tag assignment
9. Manual note
10. Extracted Bug PDF evidence
11. Audit/history
12. Reports/Exports

## Key Decisions to Confirm with Genti

The script explicitly asks Genti to confirm:

- dashboard emphasis
- DB BLOB storage acceptance
- mismatch flag governance
- first-version field comparison set
- strict versus flexible hierarchy
- extracted field editability
- status-change comment requirements
- tag governance
- note edit/version behavior
- inline PDF preview versus link/download
- audit visibility
- first required reports

## Non-Implementation Boundary Preserved

Gate 21O did not create:

- APEX pages
- database schema
- migrations
- PDF extraction behavior
- mismatch detection behavior
- workflow mutation behavior
- authorization integration

## Next Gate

Recommended next gate:

Gate 21P — Genti Review Workflow Implementation Slice Plan

Recommended scope:

- smallest implementable demo slice
- table subset
- seed data needs
- APEX page subset
- workflow actions
- acceptance criteria
- pull-and-run expectations if runtime work begins

## Gate 21O Result

Gate 21O is complete and ready to support stakeholder review or Gate 21P implementation planning.
