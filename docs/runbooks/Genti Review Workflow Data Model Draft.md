# Genti Review Workflow Data Model Draft

## Gate

Gate 21M — Genti Review Workflow Data Model Draft

## Purpose

Draft the Oracle APEX / Oracle Database relational model for the Genti review workflow before implementation.

This document translates the Gate 21L requirements capture into a first-pass data model for:

- portfolio uploads
- PDF Portfolio bug inventory
- Web-site bug inventory
- canonical bug entries
- mismatch flags
- review statuses and status history
- tags
- manual notes
- maintenance-pack hierarchy
- bug relationships
- extracted Bug PDF artifacts
- extracted Bug PDF fields
- audit events

## Change Type

Documentation/design only.

No runtime behavior changes are included in this gate.
No generated KBs or runtime artifacts should be committed for this gate.
No runtime test is required.

## Design Assumptions

1. Oracle is the internal customer.
2. Oracle APEX is the recommended first UI/workflow layer.
3. Oracle Database is the source of workflow truth.
4. Uploaded PDF Portfolios are immutable source artifacts.
5. Extracted individual Bug PDFs are derived artifacts.
6. First-version binary storage should use Oracle Database BLOBs.
7. External object/document storage remains a future option if scale, retention, or governance requires it.
8. Review status, tags, notes, hierarchy, lineage, and audit belong in structured database tables.
9. Users may annotate, classify, and review entries, but source inventory records should preserve imported values.

## Naming Conventions

- Primary keys use `<table_singular>_id`.
- Foreign keys use the referenced primary key name.
- Timestamps use `created_at`, `updated_at`, or event-specific names.
- User attribution fields use `created_by`, `updated_by`, or action-specific names.
- Controlled values should be stored in dictionary/reference tables where user configuration is expected.

## Entity Relationship Summary

```text
portfolio_uploads
  ├── portfolio_bug_inventory
  ├── bug_pdf_artifacts
  └── audit_events

website_bug_inventory
  └── bug_entries

bug_entries
  ├── mismatch_flags
  ├── bug_entry_status_history
  ├── bug_entry_tags
  ├── bug_entry_notes
  ├── bug_entry_relationships
  ├── bug_pdf_artifacts
  ├── bug_extracted_fields
  └── audit_events

maintenance_packs
  ├── bug_entries
  └── bug_entry_relationships

tag_dictionary
  └── bug_entry_tags

review_statuses
  └── bug_entry_status_history
```

## Table: `portfolio_uploads`

### Purpose

Stores uploaded PDF Portfolio source artifacts.

The uploaded portfolio is immutable and should be retained as the source of lineage for extracted Bug PDFs and PDF-derived bug inventory rows.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `portfolio_upload_id` | NUMBER / identity | Primary key. |
| `portfolio_name` | VARCHAR2 | Human-readable portfolio name. |
| `source_filename` | VARCHAR2 | Uploaded file name. |
| `content_type` | VARCHAR2 | MIME/content type. |
| `file_size_bytes` | NUMBER | Uploaded binary size. |
| `source_sha256` | VARCHAR2(64) | Hash for dedupe and lineage. |
| `portfolio_blob` | BLOB | Uploaded source PDF Portfolio binary. |
| `upload_status` | VARCHAR2 | `UPLOADED`, `PROCESSING`, `PROCESSED`, `FAILED`, etc. |
| `uploaded_by` | VARCHAR2 | User identity. |
| `uploaded_at` | TIMESTAMP | Upload timestamp. |
| `processed_at` | TIMESTAMP | Processing completion timestamp, nullable. |
| `processing_error` | CLOB | Failure detail, nullable. |

### Notes

- Source BLOBs should not be updated after upload.
- Reprocessing should create new derived records or new audit events rather than mutating source meaning.
- `source_sha256` should be indexed.

## Table: `portfolio_bug_inventory`

### Purpose

Stores bug entries as extracted/listed from the PDF Portfolio.

This table preserves PDF-side raw values for mismatch comparison.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `portfolio_bug_inventory_id` | NUMBER / identity | Primary key. |
| `portfolio_upload_id` | NUMBER | FK to `portfolio_uploads`. |
| `source_bug_identifier` | VARCHAR2 | Bug ID / patch number as shown in the PDF. |
| `maintenance_pack_label` | VARCHAR2 | MP label as extracted from PDF. |
| `maintenance_pack_path` | VARCHAR2 | Path such as `MP2 / MP2.1`. |
| `subsystem` | VARCHAR2 | Extracted subsystem/component. |
| `title` | VARCHAR2 | Extracted title. |
| `description_text` | CLOB | Extracted description if available. |
| `steps_text` | CLOB | Extracted steps if available. |
| `source_page_start` | NUMBER | First source page for the entry, nullable. |
| `source_page_end` | NUMBER | Last source page for the entry, nullable. |
| `raw_extracted_json` | CLOB | Full raw extraction payload for audit/debug. |
| `extraction_status` | VARCHAR2 | `EXTRACTED`, `PARTIAL`, `FAILED`, etc. |
| `created_at` | TIMESTAMP | Row creation timestamp. |

### Notes

- This table is source-specific and should not be treated as the canonical user-reviewed bug record.
- Use `raw_extracted_json` to preserve fields not yet modeled.

## Table: `website_bug_inventory`

### Purpose

Stores bug entries imported or extracted from the Web-site source.

This table preserves Web-site-side raw values for mismatch comparison.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `website_bug_inventory_id` | NUMBER / identity | Primary key. |
| `website_source_id` | VARCHAR2 | Identifier for crawl/import batch or source page. |
| `source_url` | VARCHAR2 | Web-site source URL or logical source reference. |
| `source_bug_identifier` | VARCHAR2 | Bug ID / patch number from Web-site. |
| `maintenance_pack_label` | VARCHAR2 | MP label from Web-site. |
| `maintenance_pack_path` | VARCHAR2 | Path such as `MP2 / MP2.1`. |
| `subsystem` | VARCHAR2 | Web-site subsystem/component. |
| `title` | VARCHAR2 | Web-site title. |
| `description_text` | CLOB | Web-site description if available. |
| `raw_extracted_json` | CLOB | Full raw import payload. |
| `import_status` | VARCHAR2 | `IMPORTED`, `PARTIAL`, `FAILED`, etc. |
| `imported_at` | TIMESTAMP | Import timestamp. |

### Notes

- Preserve raw Web-site values separately from PDF-derived values.
- Mismatch detection should compare inventory sources and write structured flags rather than overwrite either source.

## Table: `bug_entries`

### Purpose

Canonical review/workflow record for a bug entry.

This is the APEX-facing object users review, tag, annotate, and assign workflow status to.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_entry_id` | NUMBER / identity | Primary key. |
| `canonical_bug_identifier` | VARCHAR2 | Canonical bug/patch identifier. |
| `display_title` | VARCHAR2 | Review-facing title. |
| `current_review_status_id` | NUMBER | FK to `review_statuses`, nullable on import. |
| `maintenance_pack_id` | NUMBER | FK to `maintenance_packs`, nullable if unresolved. |
| `portfolio_bug_inventory_id` | NUMBER | FK to PDF-side inventory row, nullable. |
| `website_bug_inventory_id` | NUMBER | FK to Web-site-side inventory row, nullable. |
| `current_mismatch_state` | VARCHAR2 | Summary such as `MATCHED`, `PDF_ONLY`, `WEBSITE_ONLY`, `FIELD_MISMATCH`, `NEEDS_REVIEW`. |
| `review_priority` | VARCHAR2 | Optional prioritization value. |
| `is_active` | CHAR(1) | `Y`/`N`. |
| `created_at` | TIMESTAMP | Creation timestamp. |
| `created_by` | VARCHAR2 | Creator/import actor. |
| `updated_at` | TIMESTAMP | Last update timestamp. |
| `updated_by` | VARCHAR2 | Last update actor. |

### Notes

- `bug_entries` should be the workflow anchor.
- Do not store tag lists or notes directly on this table.
- `current_review_status_id` can be denormalized for fast filtering, while history remains authoritative in `bug_entry_status_history`.

## Table: `mismatch_flags`

### Purpose

Stores system-generated and/or user-reviewed mismatch findings between PDF Portfolio and Web-site inventories.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `mismatch_flag_id` | NUMBER / identity | Primary key. |
| `bug_entry_id` | NUMBER | FK to `bug_entries`. |
| `flag_type` | VARCHAR2 | `MATCHED`, `PDF_ONLY`, `WEBSITE_ONLY`, `FIELD_MISMATCH`, `NEEDS_REVIEW`. |
| `field_name` | VARCHAR2 | Field that differs, nullable for row-level flags. |
| `pdf_value` | CLOB | PDF-side value, nullable. |
| `website_value` | CLOB | Web-site-side value, nullable. |
| `severity` | VARCHAR2 | Optional severity such as `INFO`, `WARN`, `BLOCKING`. |
| `system_generated` | CHAR(1) | `Y`/`N`. |
| `review_status` | VARCHAR2 | `OPEN`, `ACCEPTED`, `DISMISSED`, `RESOLVED`. |
| `reviewed_by` | VARCHAR2 | Reviewer identity, nullable. |
| `reviewed_at` | TIMESTAMP | Review timestamp, nullable. |
| `created_at` | TIMESTAMP | Creation timestamp. |

### Notes

- Keep raw compared values for transparency.
- If mismatch flags become user-editable, preserve both system-generated and user-reviewed states.

## Table: `review_statuses`

### Purpose

Stores allowed workflow statuses.

Initial statuses should include the values requested by Genti and may include additional default workflow states.

### Seed Values

| Status Code | Display Label | Meaning |
|---|---|---|
| `NA` | `N/A` | Entry does not apply. |
| `NEEDS_FURTHER_REVIEW` | `Needs Further Review` | Entry needs more review. |
| `TEST_REQUIRED` | `Test Required` | Entry requires testing. |
| `TEST_DEFERRED` | `Test Deferred` | Testing is deferred. |
| `CONFIRMED` | `Confirmed` | Entry has been confirmed. |
| `NEW` | `New` | Newly imported/detected. |
| `IN_REVIEW` | `In Review` | User is actively reviewing. |
| `BLOCKED` | `Blocked` | Review/testing is blocked. |
| `RESOLVED` | `Resolved` | Review completed. |

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `review_status_id` | NUMBER / identity | Primary key. |
| `status_code` | VARCHAR2 | Stable code. |
| `display_label` | VARCHAR2 | User-facing label. |
| `description` | VARCHAR2 | Status meaning. |
| `display_order` | NUMBER | APEX ordering. |
| `is_active` | CHAR(1) | `Y`/`N`. |
| `created_at` | TIMESTAMP | Creation timestamp. |

### Notes

- Use a reference table instead of hardcoding statuses in APEX pages.
- Status edit permissions remain an open workflow question.

## Table: `bug_entry_status_history`

### Purpose

Stores all status changes for bug entries.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_entry_status_history_id` | NUMBER / identity | Primary key. |
| `bug_entry_id` | NUMBER | FK to `bug_entries`. |
| `from_review_status_id` | NUMBER | Previous status, nullable. |
| `to_review_status_id` | NUMBER | New status. |
| `change_reason` | VARCHAR2 | Optional reason. |
| `comment_text` | CLOB | Optional comment. |
| `changed_by` | VARCHAR2 | User identity. |
| `changed_at` | TIMESTAMP | Change timestamp. |

### Notes

- This table provides audit-friendly status history.
- The current status on `bug_entries` should be updated only by controlled workflow logic.

## Table: `tag_dictionary`

### Purpose

Stores reusable tags for review, filtering, test planning, and workflow grouping.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `tag_id` | NUMBER / identity | Primary key. |
| `tag_name` | VARCHAR2 | User-facing tag. |
| `tag_code` | VARCHAR2 | Stable normalized code. |
| `tag_description` | VARCHAR2 | Optional description. |
| `tag_color` | VARCHAR2 | Optional APEX display hint. |
| `is_active` | CHAR(1) | `Y`/`N`. |
| `created_by` | VARCHAR2 | Creator identity. |
| `created_at` | TIMESTAMP | Creation timestamp. |

### Notes

- Whether tags are admin-controlled or freeform remains open.
- For the first version, prefer controlled tags with an admin-maintained dictionary.

## Table: `bug_entry_tags`

### Purpose

Join table between bug entries and tags.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_entry_tag_id` | NUMBER / identity | Primary key. |
| `bug_entry_id` | NUMBER | FK to `bug_entries`. |
| `tag_id` | NUMBER | FK to `tag_dictionary`. |
| `applied_by` | VARCHAR2 | User identity. |
| `applied_at` | TIMESTAMP | Tag application timestamp. |
| `removed_at` | TIMESTAMP | Soft removal timestamp, nullable. |
| `removed_by` | VARCHAR2 | User identity, nullable. |

### Notes

- Use soft removal to preserve auditability.
- Enforce one active tag assignment per `bug_entry_id` + `tag_id`.

## Table: `bug_entry_notes`

### Purpose

Stores freeform manual review notes per bug entry.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_entry_note_id` | NUMBER / identity | Primary key. |
| `bug_entry_id` | NUMBER | FK to `bug_entries`. |
| `note_text` | CLOB | Freeform note body. |
| `note_type` | VARCHAR2 | Optional type such as `REVIEW`, `TESTING`, `GENERAL`. |
| `created_by` | VARCHAR2 | Author identity. |
| `created_at` | TIMESTAMP | Creation timestamp. |
| `updated_by` | VARCHAR2 | Last editor, nullable. |
| `updated_at` | TIMESTAMP | Last edit timestamp, nullable. |
| `is_deleted` | CHAR(1) | Soft delete flag. |
| `deleted_by` | VARCHAR2 | Deleter identity, nullable. |
| `deleted_at` | TIMESTAMP | Delete timestamp, nullable. |

### Notes

- Notes should not be collapsed into a single mutable field on `bug_entries`.
- If stricter audit is required, note edits can move to append-only note version rows in a later gate.

## Table: `maintenance_packs`

### Purpose

Stores maintenance-pack hierarchy nodes.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `maintenance_pack_id` | NUMBER / identity | Primary key. |
| `parent_maintenance_pack_id` | NUMBER | Self-FK for hierarchy, nullable for root. |
| `mp_code` | VARCHAR2 | Stable code such as `MP2` or `MP2.1`. |
| `mp_label` | VARCHAR2 | User-facing label. |
| `mp_path` | VARCHAR2 | Materialized path such as `MP2 / MP2.1`. |
| `display_order` | NUMBER | Sort order. |
| `is_active` | CHAR(1) | `Y`/`N`. |
| `created_at` | TIMESTAMP | Creation timestamp. |

### Notes

- A self-referencing table supports APEX tree navigation.
- `mp_path` can be materialized for filtering and display.

## Table: `bug_entry_relationships`

### Purpose

Stores relationships between bug entries and maintenance packs, and optionally between bug entries.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_entry_relationship_id` | NUMBER / identity | Primary key. |
| `source_bug_entry_id` | NUMBER | FK to `bug_entries`, nullable for MP-only relationship forms. |
| `target_bug_entry_id` | NUMBER | FK to related `bug_entries`, nullable. |
| `maintenance_pack_id` | NUMBER | FK to `maintenance_packs`, nullable. |
| `relationship_type` | VARCHAR2 | `BELONGS_TO_MP`, `RELATED_BUG`, `DUPLICATE_OF`, `BLOCKS`, etc. |
| `created_by` | VARCHAR2 | User/system actor. |
| `created_at` | TIMESTAMP | Creation timestamp. |
| `is_active` | CHAR(1) | `Y`/`N`. |

### Notes

- If strict hierarchy is confirmed, this table can be narrowed.
- If cross-links are needed, this table preserves flexibility without changing `bug_entries`.

## Table: `bug_pdf_artifacts`

### Purpose

Stores extracted individual Bug PDF derived artifacts and lineage back to the uploaded portfolio.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_pdf_artifact_id` | NUMBER / identity | Primary key. |
| `bug_entry_id` | NUMBER | FK to `bug_entries`. |
| `portfolio_upload_id` | NUMBER | FK to source `portfolio_uploads`. |
| `portfolio_bug_inventory_id` | NUMBER | FK to PDF-side inventory row. |
| `artifact_filename` | VARCHAR2 | Generated filename. |
| `artifact_sha256` | VARCHAR2(64) | Derived PDF hash. |
| `artifact_size_bytes` | NUMBER | Derived PDF size. |
| `artifact_blob` | BLOB | Extracted individual Bug PDF binary. |
| `source_page_start` | NUMBER | First source page. |
| `source_page_end` | NUMBER | Last source page. |
| `extraction_status` | VARCHAR2 | `EXTRACTED`, `FAILED`, etc. |
| `created_at` | TIMESTAMP | Artifact creation timestamp. |
| `created_by` | VARCHAR2 | System/user actor. |

### Notes

- Derived PDFs should be immutable once written.
- Do not use arbitrary user-selected directories as primary storage.
- External object/document storage can replace the BLOB with a controlled object reference in a future version.

## Table: `bug_extracted_fields`

### Purpose

Stores structured fields extracted from individual Bug PDFs.

This table supports field-level display, review, and mismatch comparison without requiring every extracted field to become a column immediately.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `bug_extracted_field_id` | NUMBER / identity | Primary key. |
| `bug_entry_id` | NUMBER | FK to `bug_entries`. |
| `bug_pdf_artifact_id` | NUMBER | FK to `bug_pdf_artifacts`. |
| `field_name` | VARCHAR2 | `Subsystem`, `Title`, `Description`, `Steps`, `Screenshots`, etc. |
| `field_value_text` | CLOB | Extracted text value. |
| `field_value_blob` | BLOB | Optional binary value for extracted images/screenshots. |
| `field_value_type` | VARCHAR2 | `TEXT`, `IMAGE`, `JSON`, etc. |
| `source_location_json` | CLOB | Page/region/offset metadata. |
| `extraction_confidence` | NUMBER | Optional deterministic/extractor score if available. |
| `created_at` | TIMESTAMP | Creation timestamp. |

### Notes

- Candidate first fields: Subsystem, Title, Description, Steps, Screenshots.
- This table avoids prematurely freezing the extracted field set.

## Table: `audit_events`

### Purpose

Stores auditable workflow and system events.

### Suggested Columns

| Column | Type Direction | Purpose |
|---|---|---|
| `audit_event_id` | NUMBER / identity | Primary key. |
| `event_type` | VARCHAR2 | Event category. |
| `entity_type` | VARCHAR2 | Table/object type. |
| `entity_id` | NUMBER | Entity identifier. |
| `bug_entry_id` | NUMBER | Optional FK context. |
| `portfolio_upload_id` | NUMBER | Optional FK context. |
| `event_payload_json` | CLOB | Structured event payload. |
| `created_by` | VARCHAR2 | Actor. |
| `created_at` | TIMESTAMP | Event timestamp. |

### Candidate Event Types

- `PORTFOLIO_UPLOADED`
- `PORTFOLIO_PROCESSED`
- `BUG_ENTRY_CREATED`
- `MISMATCH_FLAG_CREATED`
- `MISMATCH_FLAG_REVIEWED`
- `STATUS_CHANGED`
- `TAG_APPLIED`
- `TAG_REMOVED`
- `NOTE_CREATED`
- `NOTE_UPDATED`
- `BUG_PDF_EXTRACTED`
- `BUG_FIELD_EXTRACTED`

### Notes

- Audit events should be append-only.
- APEX pages can show filtered event history per bug entry.

## Recommended APEX Page Mapping

| APEX Page | Primary Tables |
|---|---|
| Dashboard | `bug_entries`, `mismatch_flags`, `review_statuses`, `audit_events` |
| Portfolio Upload | `portfolio_uploads`, `audit_events` |
| Mismatch Review | `bug_entries`, `mismatch_flags`, `portfolio_bug_inventory`, `website_bug_inventory` |
| Hierarchy Browser | `maintenance_packs`, `bug_entries`, `bug_entry_relationships` |
| Bug Entry Detail | `bug_entries`, `bug_extracted_fields`, `bug_pdf_artifacts`, `bug_entry_status_history`, `bug_entry_tags`, `bug_entry_notes`, `mismatch_flags` |
| Reports/Exports | All workflow tables, filtered by MP/status/tag/mismatch |

## First Demo Slice Recommendation

For a first APEX demo, prioritize:

1. `portfolio_uploads`
2. `portfolio_bug_inventory`
3. `website_bug_inventory`
4. `bug_entries`
5. `mismatch_flags`
6. `review_statuses`
7. `bug_entry_status_history`
8. `tag_dictionary`
9. `bug_entry_tags`
10. `bug_entry_notes`
11. `maintenance_packs`
12. `bug_pdf_artifacts`
13. `bug_extracted_fields`
14. `audit_events`

`bug_entry_relationships` can be included if cross-links are needed in the first demo. If the first demo only needs strict MP-to-bug navigation, the direct `maintenance_pack_id` on `bug_entries` may be enough initially.

## Indexing Direction

Suggested first indexes:

- `portfolio_uploads(source_sha256)`
- `portfolio_bug_inventory(portfolio_upload_id)`
- `portfolio_bug_inventory(source_bug_identifier)`
- `website_bug_inventory(source_bug_identifier)`
- `bug_entries(canonical_bug_identifier)`
- `bug_entries(current_review_status_id)`
- `bug_entries(maintenance_pack_id)`
- `mismatch_flags(bug_entry_id)`
- `mismatch_flags(flag_type)`
- `bug_entry_status_history(bug_entry_id, changed_at)`
- `bug_entry_tags(bug_entry_id)`
- `bug_entry_notes(bug_entry_id)`
- `maintenance_packs(parent_maintenance_pack_id)`
- `bug_pdf_artifacts(bug_entry_id)`
- `bug_extracted_fields(bug_entry_id, field_name)`
- `audit_events(entity_type, entity_id)`
- `audit_events(bug_entry_id, created_at)`

## Open Questions to Resolve Before Implementation

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

## Explicit Non-Implementation Boundary

This draft does not create schemas, migrations, APEX pages, storage mechanics, extraction logic, or mismatch detection logic.

It is the design basis for a later implementation gate.

## Next Gate Candidate

Gate 21N — Genti Review Workflow APEX Page Flow Draft

Possible scope:

- Dashboard page layout
- Portfolio upload page
- Mismatch review report
- Hierarchy browser
- Bug entry detail page
- Reports/export page
- role assumptions and navigation flow
