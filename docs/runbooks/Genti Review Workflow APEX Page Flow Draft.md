# Genti Review Workflow APEX Page Flow Draft

## Gate

Gate 21N — Genti Review Workflow APEX Page Flow Draft

## Purpose

Draft the first Oracle APEX page flow for the Genti review workflow before implementation.

This document translates the Gate 21L requirements capture and Gate 21M data model into an APEX-oriented demo/application flow for:

- portfolio upload
- mismatch review
- maintenance-pack hierarchy navigation
- bug entry detail review
- status, tag, and note workflow
- extracted Bug PDF preview/download
- reporting/export
- audit visibility

## Change Type

Documentation/design only.

No runtime behavior changes are included in this gate.
No APEX pages are implemented in this gate.
No generated KBs or runtime artifacts should be committed for this gate.
No runtime test is required.

## Design Inputs

- `docs/runbooks/Genti Review Workflow Requirements Capture.md`
- `docs/runbooks/Genti Review Workflow Data Model Draft.md`

## Design Assumptions

1. Oracle is the internal customer.
2. Oracle APEX is the preferred first UI/workflow layer.
3. Oracle Database is the workflow source of truth.
4. Uploaded PDF Portfolios and extracted Bug PDFs are stored as Oracle DB BLOBs in the first version.
5. Users review canonical `bug_entries`, not raw source rows directly.
6. PDF Portfolio and Web-site source inventories remain visible for comparison and audit.
7. First demo should show the workflow clearly, not every possible admin feature.
8. Page design should favor explainability over density.

## Proposed Application Navigation

```text
Dashboard
  ├── Portfolio Upload
  ├── Mismatch Review
  │     └── Bug Entry Detail
  ├── Hierarchy Browser
  │     └── Bug Entry Detail
  ├── Reports / Exports
  └── Admin / Reference Data (optional first demo)
```

## Page 1 — Dashboard

### Purpose

Provide the top-level state of the review workflow.

### Primary Audience

- project lead
- reviewer
- testing coordinator
- stakeholder watching demo progress

### Primary Tables

- `bug_entries`
- `mismatch_flags`
- `review_statuses`
- `maintenance_packs`
- `audit_events`

### Suggested Components

- corpus/portfolio summary cards
- mismatch summary cards
- review status distribution
- maintenance-pack coverage summary
- recent activity list
- links into filtered review queues

### Suggested Metrics

| Metric | Source |
|---|---|
| Uploaded portfolios | `portfolio_uploads` |
| Total bug entries | `bug_entries` |
| PDF-only entries | `mismatch_flags.flag_type = 'PDF_ONLY'` |
| Web-site-only entries | `mismatch_flags.flag_type = 'WEBSITE_ONLY'` |
| Field mismatches | `mismatch_flags.flag_type = 'FIELD_MISMATCH'` |
| Needs review | `bug_entries.current_review_status_id` or mismatch review state |
| Test required | `review_statuses.status_code = 'TEST_REQUIRED'` |
| Confirmed | `review_statuses.status_code = 'CONFIRMED'` |

### Primary Actions

- upload new portfolio
- open mismatch review
- open hierarchy browser
- open entries filtered by status/mismatch
- open reports/export page

### Demo Framing

The dashboard should make the system look like a controlled review workflow, not a chatbot.

## Page 2 — Portfolio Upload

### Purpose

Allow upload of a PDF Portfolio and show processing state.

### Primary Tables

- `portfolio_uploads`
- `audit_events`

### Suggested Components

- upload form
- uploaded portfolio list
- processing status
- file hash / size metadata
- processing error panel if failed

### Fields Displayed

- portfolio name
- source filename
- upload status
- uploaded by
- uploaded at
- file size
- SHA-256 hash
- processed at

### Primary Actions

- upload portfolio
- view portfolio metadata
- download original portfolio
- start/retry processing in a later implementation gate

### Implementation Boundary

This page flow draft does not define the actual processing job mechanics.

## Page 3 — Mismatch Review

### Purpose

Provide the main queue for resolving differences between PDF Portfolio inventory and Web-site inventory.

### Primary Tables

- `bug_entries`
- `mismatch_flags`
- `portfolio_bug_inventory`
- `website_bug_inventory`
- `review_statuses`
- `maintenance_packs`

### Suggested Layout

Interactive report or grid with filters.

### Suggested Columns

| Column | Purpose |
|---|---|
| Bug ID | Canonical bug identifier. |
| MP Path | Maintenance-pack hierarchy. |
| Mismatch State | Summary mismatch classification. |
| Mismatch Type | Specific flag type. |
| Field Name | Field that differs, if field-level mismatch. |
| PDF Value | Source portfolio value. |
| Web-site Value | Web-site value. |
| Review Status | Current workflow status. |
| Tags | Current tag indicators. |
| Last Updated | Last review/action timestamp. |

### Filters

- mismatch type
- review status
- maintenance pack
- subsystem
- tag
- reviewer
- open/resolved mismatch state

### Primary Actions

- open Bug Entry Detail
- set review status for selected entry if allowed
- mark mismatch flag as accepted/dismissed/resolved if allowed
- bulk tag selected entries if allowed in later implementation
- export filtered mismatch report

### Demo Behavior

For the first demo, prioritize:

1. visible mismatch categories
2. side-by-side PDF/Web-site values
3. single-click entry detail navigation
4. status update path
5. tag/note visibility

## Page 4 — Hierarchy Browser

### Purpose

Allow navigation by maintenance-pack hierarchy such as `MP2 / MP2.1 / Bug 134`.

### Primary Tables

- `maintenance_packs`
- `bug_entries`
- `bug_entry_relationships`
- `review_statuses`
- `mismatch_flags`

### Suggested Layout

Two-pane layout:

```text
Left: Maintenance Pack Tree
Right: Bug Entries for selected MP
```

### Tree Behavior

- show root MP nodes
- expand child maintenance packs
- display bug counts by node
- optionally display mismatch/status counts by node

### Bug List Columns

- Bug ID
- Title
- Subsystem
- Review Status
- Mismatch State
- Tags

### Primary Actions

- select maintenance pack
- open bug entry
- navigate sibling bugs
- return to parent MP

### Open Design Choice

If a bug can belong to multiple maintenance packs, use `bug_entry_relationships` for MP membership.
If hierarchy is strict, `bug_entries.maintenance_pack_id` may be enough for first implementation.

## Page 5 — Bug Entry Detail

### Purpose

Provide the central review screen for a single bug entry.

### Primary Tables

- `bug_entries`
- `portfolio_bug_inventory`
- `website_bug_inventory`
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

### Suggested Layout

```text
Header
  Bug ID | Title | MP Path | Current Status | Mismatch State

Left/Main
  Extracted Fields
  PDF vs Web-site Comparison
  Steps / Description
  Screenshots or extracted visual evidence

Right/Side Panel
  Status selector
  Tags
  Manual notes
  Extracted Bug PDF link/preview
  Audit/history
```

### Header Fields

- canonical bug identifier
- display title
- MP path breadcrumb
- current review status
- mismatch state
- subsystem

### Extracted Field Section

Show fields from `bug_extracted_fields`, including:

- Subsystem
- Title
- Description
- Steps
- Screenshots

### Source Comparison Section

Show PDF Portfolio and Web-site values side by side when both exist.

Suggested comparison fields:

- bug identifier
- maintenance pack path
- subsystem
- title
- description

### Workflow Section

Allow controlled user actions:

- set status
- add/remove tags
- add manual note
- resolve or disposition mismatch flag if allowed

### PDF Section

Show:

- source portfolio link/download
- extracted Bug PDF link/download
- optional embedded preview if APEX environment supports it cleanly

### Audit Section

Show chronological events:

- entry created
- mismatch flag created
- status changed
- tag applied/removed
- note created/updated
- PDF extracted
- extracted field created

### First Demo Behavior

The first demo should show:

1. one bug with a PDF-only or field mismatch flag
2. extracted fields displayed clearly
3. status changed to `Needs Further Review` or `Test Required`
4. a tag added
5. a manual note added
6. extracted Bug PDF link or preview shown
7. audit/history reflecting the actions

## Page 6 — Reports / Exports

### Purpose

Provide exportable review and testing reports.

### Primary Tables

- `bug_entries`
- `mismatch_flags`
- `review_statuses`
- `bug_entry_tags`
- `tag_dictionary`
- `maintenance_packs`
- `bug_entry_notes`
- `audit_events`

### Suggested Reports

- mismatch report
- status summary report
- test-required report
- deferred-testing report
- confirmed entries report
- tag-based report
- maintenance-pack review progress report

### Export Formats

First-version candidates:

- CSV from APEX report
- PDF report if needed later
- Excel-compatible export if approved

### Demo Behavior

For first demo, show a filtered mismatch report and a filtered test-required report.

## Optional Page 7 — Admin / Reference Data

### Purpose

Manage controlled values if needed.

### Primary Tables

- `review_statuses`
- `tag_dictionary`

### First Demo Recommendation

Do not prioritize this page unless Genti asks for configurable statuses/tags in the first demo.

Seed statuses and tags can be preloaded for the first workflow demo.

## Suggested User Flow — First Demo

```text
1. Open Dashboard
2. Show total entries, mismatch counts, and status counts
3. Open Mismatch Review
4. Filter to FIELD_MISMATCH or PDF_ONLY
5. Open a Bug Entry Detail
6. Show extracted Subsystem, Title, Description, Steps, Screenshots
7. Show extracted Bug PDF link/preview
8. Set status to Test Required
9. Add tag such as Needs Validation
10. Add manual note
11. Show audit/history updated
12. Return to Dashboard and show changed status count
13. Open Reports / Exports and show filtered review report
```

## Suggested Initial Roles

| Role | Intended Capabilities |
|---|---|
| Viewer | View dashboard, reports, bug details, PDFs. |
| Reviewer | Change status, add tags, add notes, disposition mismatch flags. |
| Admin | Manage status/tag reference data, perform upload/process actions. |

## Authorization Open Questions

- Which Oracle/internal auth model will be used?
- Are roles mapped from Oracle groups?
- Can all reviewers see all maintenance packs?
- Who can upload portfolios?
- Who can change status values or tags?
- Who can export reports?

## Page-to-Table Mapping Summary

| Page | Primary Tables |
|---|---|
| Dashboard | `bug_entries`, `mismatch_flags`, `review_statuses`, `maintenance_packs`, `audit_events` |
| Portfolio Upload | `portfolio_uploads`, `audit_events` |
| Mismatch Review | `bug_entries`, `mismatch_flags`, `portfolio_bug_inventory`, `website_bug_inventory`, `review_statuses`, `maintenance_packs` |
| Hierarchy Browser | `maintenance_packs`, `bug_entries`, `bug_entry_relationships`, `review_statuses`, `mismatch_flags` |
| Bug Entry Detail | `bug_entries`, `bug_extracted_fields`, `bug_pdf_artifacts`, `bug_entry_status_history`, `bug_entry_tags`, `bug_entry_notes`, `mismatch_flags`, `audit_events` |
| Reports / Exports | workflow and reporting tables |
| Admin / Reference Data | `review_statuses`, `tag_dictionary` |

## First Implementation Slice Recommendation

When implementation begins, build only the minimum viable APEX path:

1. Dashboard summary cards
2. Mismatch Review report
3. Bug Entry Detail page
4. status update mechanism
5. tag display and assignment
6. manual note creation
7. extracted Bug PDF link/download
8. basic audit event display

Defer:

- full admin screens
- bulk update actions
- embedded PDF preview if environment complicates it
- advanced report formatting
- role-complex authorization beyond basic demo needs

## Explicit Non-Implementation Boundary

This draft does not create:

- APEX pages
- database schema
- migrations
- processing jobs
- upload handlers
- PDF extraction logic
- mismatch detection logic
- authorization integration

It defines the page-flow design basis for a later implementation gate.

## Next Gate Candidate

Gate 21O — Genti Review Workflow Demo Script Draft

Possible scope:

- live demo sequence
- demo data assumptions
- talking points
- page-by-page script
- expected user questions
- implementation blockers to clarify with Genti
