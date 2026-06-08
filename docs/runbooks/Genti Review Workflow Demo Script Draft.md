# Genti Review Workflow Demo Script Draft

## Gate

Gate 21O — Genti Review Workflow Demo Script Draft

## Purpose

Draft a live demo script for the Genti review workflow before implementation.

This document turns the Gate 21L requirements, Gate 21M data model, and Gate 21N APEX page flow into a demo-ready narrative that can be used to align expectations with Genti before building screens or workflow behavior.

## Change Type

Documentation/design only.

No runtime behavior changes are included in this gate.
No APEX pages are implemented in this gate.
No generated KBs or runtime artifacts should be committed for this gate.
No runtime test is required.

## Design Inputs

- `docs/runbooks/Genti Review Workflow Requirements Capture.md`
- `docs/runbooks/Genti Review Workflow Data Model Draft.md`
- `docs/runbooks/Genti Review Workflow APEX Page Flow Draft.md`

## Demo Objective

Show that the upgrade impact tool can support a structured human review workflow for Oracle internal use by connecting:

1. uploaded PDF Portfolio source material
2. Web-site bug inventory
3. mismatch detection/review
4. maintenance-pack hierarchy navigation
5. bug-level review status
6. tags
7. manual notes
8. extracted Bug PDF evidence
9. audit/history
10. reports/exports

The demo should prove workflow clarity, not final production completeness.

## Demo Framing

### Opening Message

This demo shows the proposed review workflow for comparing PDF Portfolio bug entries against Web-site bug entries, navigating by maintenance-pack hierarchy, and recording review decisions in an Oracle APEX application backed by Oracle Database.

### Key Positioning

- The PDF Portfolio remains the immutable source artifact.
- Extracted Bug PDFs are derived artifacts with lineage.
- The Web-site bug inventory remains separately preserved.
- Reviewers work from canonical bug entries.
- Status, tags, notes, mismatch decisions, and audit history are stored as structured workflow data.
- The first storage recommendation is Oracle Database BLOBs for uploaded portfolios and extracted Bug PDFs.
- Oracle object/document storage remains a future option if scale or governance requires it.

## Demo Data Assumptions

The demo should use a small curated set of entries from the validated actual corpus.

Suggested demo data shape:

| Demo Data Item | Suggested Count | Purpose |
|---|---:|---|
| Uploaded PDF Portfolio | 1 | Show source artifact. |
| Maintenance packs | 2–3 | Show hierarchy navigation. |
| Bug entries | 8–12 | Enough to show filters without clutter. |
| PDF-only mismatch | 1–2 | Show PDF-side-only finding. |
| Web-site-only mismatch | 1–2 | Show Web-site-side-only finding. |
| Field mismatch | 2–3 | Show side-by-side comparison. |
| Matched entry | 1–2 | Show normal aligned case. |
| Extracted Bug PDFs | 2–3 | Show derived evidence. |
| Tags | 3–5 | Show workflow grouping. |
| Notes | 1–2 | Show manual review trail. |

## Suggested Seed Statuses

Use these status values for the demo:

- `New`
- `Needs Further Review`
- `Test Required`
- `Test Deferred`
- `Confirmed`
- `N/A`
- `Blocked`
- `Resolved`

Genti-requested values should be visible:

- `N/A`
- `Needs Further Review`
- `Test Required`
- `Test Deferred`
- `Confirmed`

## Suggested Seed Tags

Use simple, business-readable tags:

- `Needs Validation`
- `Regression Risk`
- `Customer Visible`
- `Testing Candidate`
- `Documentation Check`

Final tag governance remains open.

## Live Demo Script

### Step 1 — Dashboard

#### Action

Open the APEX Dashboard.

#### Show

- uploaded portfolio count
- total bug entries
- mismatch counts
- review status distribution
- maintenance-pack coverage
- recent activity

#### Talking Points

This is the review control center. It shows where the review stands, how many entries need attention, and where reviewers should start.

We are not asking users to search through raw PDFs manually. The workflow organizes the entries into review queues.

#### Expected Reaction

Genti should confirm whether these summary metrics match how the team thinks about the review process.

#### Question to Ask

Are these the right dashboard counts, or should the first dashboard emphasize testing progress, mismatch resolution, or maintenance-pack coverage differently?

## Step 2 — Portfolio Upload View

### Action

Open Portfolio Upload.

### Show

- uploaded source filename
- upload status
- file size
- SHA-256 hash
- uploaded by / uploaded at
- processed status
- original portfolio download/link

### Talking Points

The uploaded PDF Portfolio is treated as an immutable source artifact. We keep it intact and link all extracted Bug PDFs and PDF-derived bug inventory rows back to it.

### Expected Reaction

Genti should confirm whether keeping the source portfolio as a stored artifact in Oracle Database is acceptable for the first internal version.

### Question to Ask

Is Oracle Database BLOB storage acceptable for the first internal version, or do we need to align immediately with an approved object/document storage service?

## Step 3 — Mismatch Review Queue

### Action

Open Mismatch Review.

### Show

- interactive report/grid
- filter by mismatch type
- `PDF_ONLY`
- `WEBSITE_ONLY`
- `FIELD_MISMATCH`
- `NEEDS_REVIEW`
- bug ID
- MP path
- current status
- tag indicators

### Talking Points

This queue is where reviewers work the differences between the PDF Portfolio and the Web-site inventory.

The system keeps both source values visible. It does not hide the original PDF value or overwrite the Web-site value.

### Expected Reaction

Genti should validate whether these mismatch categories are sufficient for the first demo.

### Question to Ask

Should mismatch flags be system-generated only, or should reviewers be able to add or modify flags manually?

## Step 4 — Field Mismatch Example

### Action

Filter to `FIELD_MISMATCH` and open one bug entry.

### Show

- PDF-side field value
- Web-site-side field value
- field name that differs
- current mismatch review state

### Talking Points

This is the side-by-side comparison view. The reviewer can see exactly which field differs and make a review decision without losing source lineage.

### Expected Reaction

Genti should confirm which fields are important enough for first-version comparison.

### Question to Ask

Which fields must be compared in the first version: bug ID, title, subsystem, MP path, description, steps, or others?

## Step 5 — Hierarchy Browser

### Action

Open Hierarchy Browser.

### Show

- maintenance-pack tree
- selected MP node
- bug entries under the selected node
- breadcrumb such as `MP2 / MP2.1 / Bug 134`

### Talking Points

This supports the navigation model Genti described: move from a major maintenance pack to a specific maintenance pack, then into bug entries, and back again.

### Expected Reaction

Genti should validate whether hierarchy should be strict or whether bugs can appear under multiple maintenance packs.

### Question to Ask

Can a bug belong to more than one maintenance pack, or is the hierarchy strictly one parent path per bug?

## Step 6 — Bug Entry Detail

### Action

Open a bug from the hierarchy or mismatch queue.

### Show

Header:

- bug ID
- title
- MP path
- subsystem
- current status
- mismatch state

Main sections:

- extracted fields
- PDF vs Web-site comparison
- description
- steps
- screenshots or visual evidence if available

Side panel:

- status selector
- tags
- manual notes
- extracted Bug PDF link/download or preview
- audit/history

### Talking Points

This is the main reviewer workspace. The user can see the extracted data, the source comparison, the derived Bug PDF, and the workflow controls in one place.

### Expected Reaction

Genti should confirm which fields are mandatory for the first usable screen.

### Question to Ask

Should extracted fields be editable, or should users only add notes/status/tags while preserving extracted fields as read-only evidence?

## Step 7 — Status Update

### Action

Change status from `New` or `Needs Further Review` to `Test Required`.

### Show

- updated status on the Bug Entry Detail screen
- status history row
- audit event

### Talking Points

Status changes are workflow data. They should be tracked historically, not overwritten without a trail.

### Expected Reaction

Genti should validate whether status changes require comments.

### Question to Ask

Should every status change require a comment, or only certain transitions such as `Test Deferred` or `Confirmed`?

## Step 8 — Tag Assignment

### Action

Add tag `Needs Validation` or `Regression Risk`.

### Show

- tag shown on detail page
- tag visible back in mismatch list/report
- audit event if included in the demo

### Talking Points

Tags support grouping, filtering, risk marking, and test planning.

### Expected Reaction

Genti should confirm whether tags should be freeform or controlled.

### Question to Ask

Should tags be controlled by an admin-maintained dictionary, or can reviewers create freeform tags?

## Step 9 — Manual Note

### Action

Add a manual review note.

Suggested note:

```text
Needs validation against MP2.1 test environment before confirmation.
```

### Show

- note saved on detail page
- author and timestamp
- optional audit event

### Talking Points

Manual notes capture human judgment without mutating the imported source values.

### Expected Reaction

Genti should confirm whether notes are editable or append-only.

### Question to Ask

Should notes be editable, append-only, or versioned?

## Step 10 — Extracted Bug PDF Evidence

### Action

Open or preview the extracted Bug PDF.

### Show

- extracted Bug PDF link/download or embedded preview
- lineage back to uploaded source portfolio
- page range if available

### Talking Points

The extracted Bug PDF is a derived artifact. The original portfolio remains preserved, and the extracted PDF gives reviewers focused evidence for one bug.

### Expected Reaction

Genti should confirm preferred preview behavior.

### Question to Ask

Should the first version embed the Bug PDF preview inline, or is opening/downloading the extracted PDF sufficient?

## Step 11 — Audit / History

### Action

Open or scroll to the audit/history section.

### Show

- bug entry created
- mismatch flag created
- status changed
- tag applied
- note created
- Bug PDF extracted

### Talking Points

The workflow is auditable. Review decisions are preserved with user and time context.

### Expected Reaction

Genti should validate the level of history that needs to be visible to reviewers.

### Question to Ask

Should audit/history be visible to all reviewers, or only admins/managers?

## Step 12 — Reports / Exports

### Action

Open Reports / Exports.

### Show

- filtered mismatch report
- test-required report
- status summary report
- maintenance-pack progress report

### Talking Points

The goal is not just to review entries one by one. The workflow should also produce review and testing outputs the team can act on.

### Expected Reaction

Genti should confirm which reports matter most for first release.

### Question to Ask

Which report is most important for the next demo: mismatch report, test-required report, status summary, or maintenance-pack progress?

## Closing Summary

### Closing Message

The proposed workflow keeps source artifacts intact, gives reviewers a canonical bug entry workspace, supports status/tags/notes, exposes mismatch evidence, and preserves audit history. The next decision is which parts of this flow must be implemented first for the internal Oracle demo.

## Expected User Questions

### Q1: Where are the extracted Bug PDFs stored?

Recommended answer:

For the first internal Oracle version, the recommendation is Oracle Database BLOB storage for both uploaded portfolios and extracted Bug PDFs, with metadata, hashes, lineage, and audit in Oracle Database tables. Approved Oracle object/document storage remains a future option if scale or governance requires it.

### Q2: Can reviewers edit extracted values?

Recommended answer:

The safer first design is to keep extracted values read-only and allow users to add statuses, tags, notes, and mismatch dispositions. If editing extracted fields is required, edits should be modeled separately as reviewed/curated values with audit history.

### Q3: Can we compare PDF and Web-site values side by side?

Recommended answer:

Yes. The data model keeps PDF Portfolio inventory and Web-site inventory separate, then links them through canonical bug entries and mismatch flags so both source values can be displayed side by side.

### Q4: Can a bug appear in more than one maintenance pack?

Recommended answer:

The draft supports both possibilities. If hierarchy is strict, `bug_entries.maintenance_pack_id` is enough. If cross-links or multiple MP membership are needed, `bug_entry_relationships` supports that.

### Q5: Can status values and tags be configured?

Recommended answer:

The draft uses `review_statuses` and `tag_dictionary` tables so controlled values can be configured. Whether users or only admins can manage those values is an open workflow decision.

### Q6: Is this ready to implement?

Recommended answer:

The design is ready for review, but implementation should wait until open decisions are confirmed: status governance, tag governance, note behavior, hierarchy rules, storage acceptance, APEX environment, and first-demo field requirements.

## Implementation Blockers to Clarify

Before implementation, confirm:

1. APEX target environment.
2. Oracle authentication/authorization model.
3. User roles and permissions.
4. DB BLOB storage acceptance for first version.
5. Expected portfolio and extracted PDF volume.
6. Status governance.
7. Tag governance.
8. Note edit/version behavior.
9. Strict versus flexible hierarchy.
10. Required fields for Bug Entry Detail.
11. Inline PDF preview versus link/download.
12. Required first reports.

## Recommended First Implementation Slice After Approval

After Genti confirms the workflow, implement the smallest demoable vertical slice:

1. seed/upload one portfolio record
2. load a small PDF/Web-site inventory set
3. create canonical bug entries
4. create mismatch flags
5. create maintenance-pack hierarchy
6. show Dashboard counts
7. show Mismatch Review list
8. show Bug Entry Detail
9. allow status update
10. allow tag assignment
11. allow manual note creation
12. show extracted Bug PDF link/download
13. show audit/history

## Explicit Non-Implementation Boundary

This draft does not create:

- APEX pages
- database schema
- migrations
- PDF extraction behavior
- mismatch detection behavior
- workflow mutation behavior
- authorization integration

It defines the demo narrative and decision points for stakeholder confirmation.

## Next Gate Candidate

Gate 21P — Genti Review Workflow Implementation Slice Plan

Possible scope:

- smallest implementable demo slice
- table subset
- seed data needs
- APEX page subset
- workflow actions
- acceptance criteria
- pull-and-run expectations if runtime work begins
