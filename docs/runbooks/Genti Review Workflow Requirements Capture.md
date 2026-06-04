# Genti Review Workflow Requirements Capture

## Purpose

Capture the workflow, storage, navigation, and UI requirements raised by Genti for the internal Oracle upgrade impact tool.

This document converts customer feedback into explicit requirements before implementation.

## Source

Genti requested clarification on the following areas:

- mismatch handling between PDF Portfolio and Web-site bug lists
- entry-level workflow statuses
- tags per entry
- manual review notes
- hierarchy navigation
- extracted Bug PDF storage
- Bug PDF component display
- hosting and storage decisions

## Current Project Position

The project currently has a working technical demo foundation.

Validated actual corpus state:

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

The next step is to confirm review workflow, screen layout, storage, and hosting expectations before implementing APEX screens or workflow tables.

## Requirement Group 1 — Portfolio/Web-site Mismatch Flags

### Requirement

The tool should detect and flag mismatches between the bug list in the PDF Portfolio and the bug list from the Web-site.

### Initial Flag Types

| Flag | Meaning |
|---|---|
| `MATCHED` | Entry appears in both sources and aligns. |
| `PDF_ONLY` | Entry appears in the PDF Portfolio but not the Web-site list. |
| `WEBSITE_ONLY` | Entry appears in the Web-site list but not the PDF Portfolio. |
| `FIELD_MISMATCH` | Entry exists in both sources but one or more fields differ. |
| `NEEDS_REVIEW` | Entry requires manual user review. |

### User Action

Users should be able to review flagged entries and assign a workflow status.

### Open Questions

- Which mismatch types are highest priority?
- Should mismatch flags be system-generated only, user-editable, or both?
- Should mismatch reports be exportable?
- Should the system preserve the raw values from both sources for comparison?

## Requirement Group 2 — Entry Review Status

### Requirement

Each bug entry should support a user-controlled review status.

### Initial Status Values

| Status | Meaning |
|---|---|
| `N/A` | Entry does not apply. |
| `Needs Further Review` | Entry requires additional review. |
| `Test Required` | Entry requires testing. |
| `Test Deferred` | Testing is deferred. |
| `Confirmed` | Entry has been confirmed. |

### Recommended Additional Status Values

| Status | Meaning |
|---|---|
| `New` | Newly imported or detected entry. |
| `In Review` | User is actively reviewing the entry. |
| `Blocked` | Review or testing is blocked. |
| `Resolved` | Review has been completed. |

### Data Model Direction

Statuses should be stored as structured workflow state with status history.

Suggested tables:

- `bug_entries`
- `bug_entry_status_history`

### Open Questions

- Who can change status?
- Should status changes require comments?
- Should status history be visible to users?
- Should status values be configurable by an admin?

## Requirement Group 3 — Tags Per Entry

### Requirement

Each entry should support one or more tags.

### Purpose

Tags support:

- filtering
- workflow grouping
- risk marking
- test planning
- review organization

### Data Model Direction

Suggested tables:

- `tag_dictionary`
- `bug_entry_tags`

### Open Questions

- Should tags be freeform or controlled vocabulary?
- Who can create new tags?
- Should tags be reusable across maintenance packs?
- Should tag changes be audited?

## Requirement Group 4 — Manual Review Notes

### Requirement

Each entry should support freeform manual review notes.

### Data Model Direction

Notes should be stored separately from the bug entry to preserve authorship and history.

Suggested table:

- `bug_entry_notes`

Suggested fields:

| Field | Purpose |
|---|---|
| `note_id` | Unique note identifier. |
| `bug_entry_id` | Linked bug entry. |
| `note_text` | Freeform note body. |
| `created_by` | User who created the note. |
| `created_at` | Creation timestamp. |
| `updated_by` | Last user to update the note. |
| `updated_at` | Last update timestamp. |

### Open Questions

- Are notes editable after creation?
- Do notes need audit history?
- Should notes be exportable?
- Should notes support multiple entries per bug, or one current note field?

## Requirement Group 5 — Hierarchy and Navigation

### Requirement

The tool should support navigation across maintenance-pack hierarchy and bug entries.

### Tree Model

```text
MP 2
  MP 2.1
    Bug 134
    Bug 354
  MP 2.2
    Bug 042
    Bug 031
```

### Path Model

```text
MP2 / MP2.1 / Bug 134
MP2 / MP2.1 / Bug 354
MP2 / MP2.2 / Bug 042
MP2 / MP2.2 / Bug 031
```

### Navigation Requirements

Users should be able to:

- navigate from major MP to specific MP
- navigate from MP to bug entries
- navigate from bug entry back to parent MP
- move between sibling bug entries
- view full hierarchy path on each bug detail screen

### Data Model Direction

Suggested tables:

- `maintenance_packs`
- `bug_entries`
- `bug_entry_relationships`

### Open Questions

- Can a bug belong to more than one maintenance pack?
- Are relationships strictly hierarchical, or can cross-links exist?
- Should hierarchy be imported from source files or curated by users?
- Should hierarchy be shown as a tree, breadcrumbs, or both?

## Requirement Group 6 — Extracted Bug PDF Storage

### Requirement

The uploaded PDF Portfolio should be treated as the immutable source artifact.

Extracted individual Bug PDFs should be treated as generated derived artifacts.

### Recommended Oracle-Native Storage Direction

For an internal Oracle application, the preferred initial architecture is:

| Layer | Recommendation |
|---|---|
| UI and workflow | Oracle APEX. |
| Metadata | Oracle Database. |
| Status, tags, notes, hierarchy, lineage, audit | Oracle Database tables. |
| Uploaded portfolios | Oracle DB BLOBs for first version. |
| Extracted Bug PDFs | Oracle DB BLOBs for first version. |

### Alternative Storage Direction

If document volume, retention policy, or governance requires external storage:

| Layer | Recommendation |
|---|---|
| PDF binary storage | Approved Oracle document or object storage. |
| Application metadata | Oracle Database. |
| Object references | Stored in database. |
| Hashes and lineage | Stored in database. |

### Recommended First Version

Use Oracle DB BLOB storage for uploaded portfolios and extracted Bug PDFs.

Keep external object or document storage as a future option if scale or governance requires it.

### Open Questions

- Expected number and size of portfolios?
- Expected number and size of extracted Bug PDFs?
- Retention requirements?
- Download requirements?
- Preview requirements?
- Audit requirements?
- Is DB BLOB storage acceptable for the first internal version?

## Requirement Group 7 — Bug Detail Screen

### Requirement

The tool should provide a Bug detail view showing extracted and reviewable fields.

### Candidate Fields

| Field | Purpose |
|---|---|
| Bug ID / Patch number | Primary bug identifier. |
| Maintenance pack path | Hierarchy context. |
| Subsystem | Extracted component field. |
| Title | Extracted title. |
| Description | Extracted description. |
| Steps | Extracted reproduction or validation steps. |
| Screenshots | Extracted or linked visual evidence. |
| Status | User-controlled review status. |
| Tags | User-controlled tags. |
| Manual review notes | User-entered notes. |
| Mismatch flags | System-generated or review flags. |
| Source portfolio | Link to uploaded source portfolio. |
| Extracted Bug PDF | Link or preview for derived PDF. |
| Audit/history | Status and review history. |

### APEX Page Direction

Candidate APEX pages:

| Page | Purpose |
|---|---|
| Dashboard | Corpus, mismatch, and workflow summary. |
| Portfolio Upload | Upload portfolio and start processing. |
| Mismatch Review | Review PDF/Web-site mismatches. |
| Hierarchy Browser | Navigate MP and bug hierarchy. |
| Bug Entry Detail | Review extracted fields, status, tags, notes, PDF. |
| Reports/Exports | Export mismatch, review, or testing reports. |

### Open Questions

- Which fields are mandatory for the first demo?
- Should screenshots be previewed inline?
- Should PDF preview be embedded or opened separately?
- Should users edit extracted fields or only annotate and review them?
- Should the Bug detail screen show side-by-side PDF Portfolio and Web-site values?

## Hosting Direction

### Recommended Hosting Model

Since this is an internal Oracle customer, APEX is a strong fit.

Recommended initial stack:

| Component | Recommendation |
|---|---|
| Application | Oracle APEX. |
| Database | Oracle Database. |
| Document storage | DB BLOBs for first version. |
| API/Web access | ORDS where needed. |
| Authentication | Customer-approved Oracle/internal auth model. |

### Why APEX

APEX supports:

- internal Oracle-native web app
- database-backed workflow
- forms and reports
- authentication and authorization integration
- file upload and download patterns
- fast UI iteration

### Open Hosting Questions

- Target APEX environment?
- Authentication and authorization model?
- User roles?
- Database schema ownership?
- Storage limits for BLOBs?
- Backup and retention requirements?
- Promotion path from demo to production?

## Proposed Next Demo

The next demo should show:

1. Portfolio/Web-site mismatch review list
2. Entry status assignment
3. Tags
4. Manual notes
5. Hierarchy browser
6. Bug detail screen mockup
7. Extracted Bug PDF link or preview
8. APEX hosting/storage recommendation

## Stop Condition

Do not implement the workflow until these items are confirmed:

- status values
- tag model
- note behavior
- hierarchy rules
- PDF storage choice
- APEX environment
- Bug detail screen fields

## Next Gate

Gate 21M — Genti Review Workflow Data Model Draft
