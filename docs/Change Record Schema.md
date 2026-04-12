# Change Record Schema v1

**Purpose:** Normalize Oracle KB-derived upgrade changes into structured records suitable for deterministic comparison, user-facing reporting, and audit traceability.

---

# 1. Schema Design Goals

The schema must support:

* deterministic comparison logic
* user-facing display in the application UI
* traceability to Oracle KB sources
* risk classification
* action-oriented reporting
* admin-only audit and maintenance workflows

This schema is intentionally split into two layers:

* User-facing fields
* Internal / admin fields

---

# 2. Top-Level Schema

```yaml id="j5z8pn"
change_record:

  change_id:
  schema_version:

  source:
    kb_article_number:
    kb_title:
    kb_url:
    published_date:
    source_document_type:

  applicability:
    product_line:
    application_name:
    module_name:
    version_from:
    version_to:
    functional_area:

  classification:
    change_taxonomy:
    severity:
    impact_type:

  user_view:
    headline:
    plain_language_summary:
    business_impact_summary:
    technical_impact_summary:
    recommended_action:
    user_confidence_note:

  comparison_targets:
    affected_objects:
      - object_name:
        object_type:
    affected_features:
      - feature_name:
    affected_integrations:
      - integration_surface:

  evidence:
    quoted_reference_text:
    reference_section:
    extraction_notes:

  assumptions:
    standard_usage_assumed:
    customization_review_required:
    integration_review_required:

  admin:
    ingestion_run_id:
    extraction_method:
    extraction_status:
    normalization_status:
    review_status:
    created_utc:
    updated_utc:
    content_hash:
```

---

# 3. User-Facing Fields

These fields are intended for direct display in the primary UI.

## headline

Short UI title.

Example:

```text id="z0xvzc"
Invoice validation behavior updated
```

## plain_language_summary

Simple explanation for end users.

Example:

```text id="s1e4b1"
Oracle changed invoice validation behavior in this update. Customers using standard invoice approval flows may need to review how duplicate invoices are identified.
```

## business_impact_summary

User-facing functional explanation.

Example:

```text id="8h2g3g"
This may affect invoice processing workflows and validation outcomes for Accounts Payable teams.
```

## technical_impact_summary

Condensed technical explanation.

Example:

```text id="jhnq2x"
Validation logic for invoice records was modified. Custom validation scripts and related integrations should be reviewed.
```

## recommended_action

Action-oriented field for report and UI display.

Example:

```text id="of8wq8"
Review invoice validation workflows and test any custom AP validation logic before upgrade.
```

## user_confidence_note

Human-readable traceability note.

Example:

```text id="nrddz8"
Based on Oracle KB 2943812.1 and current-state data provided for Accounts Payable.
```

---

# 4. Comparison Engine Fields

These fields support deterministic applicability logic.

## product_line

Example:

```text id="0itcvr"
PeopleSoft
```

## application_name

Example:

```text id="t44l3a"
Accounts Payable
```

## module_name

Example:

```text id="7cz0m7"
Invoice Processing
```

## version_from / version_to

Defines applicability window.

Example:

```text id="gkq4lh"
9.2.38 → 9.2.39
```

## affected_objects

Objects used for technical comparison.

Example:

```yaml id="n30293"
affected_objects:
  - object_name: AP_INVOICE
    object_type: table
  - object_name: AP_VALIDATION_RULE
    object_type: workflow_rule
```

## affected_features

Functional matching hooks.

Example:

```yaml id="wv7fuz"
affected_features:
  - feature_name: duplicate invoice detection
  - feature_name: invoice approval routing
```

## affected_integrations

Used to detect interface relevance.

Example:

```yaml id="526zvy"
affected_integrations:
  - integration_surface: invoice create API
  - integration_surface: payment schedule export
```

---

# 5. Classification Fields

## change_taxonomy

Allowed values:

* CONFIGURATION
* BEHAVIORAL
* SCHEMA
* INTEGRATION
* SECURITY
* PERFORMANCE
* DEPRECATION
* REPORTING
* WORKFLOW
* UI
* DOCUMENTATION

## severity

Allowed values:

* LOW
* MEDIUM
* HIGH

## impact_type

Allowed values:

* FUNCTIONAL
* TECHNICAL
* BOTH

---

# 6. Evidence Fields

These exist to support UI trust and report traceability.

## quoted_reference_text

Short source excerpt used to justify the finding.

## reference_section

Oracle document section label if available.

## extraction_notes

Internal notes on how the record was created.

---

# 7. Assumption Flags

These fields support automatic report transparency.

## standard_usage_assumed

Boolean

## customization_review_required

Boolean

## integration_review_required

Boolean

---

# 8. Admin / Internal Fields

These fields are not required in the user-facing UI by default.

## ingestion_run_id

Links record to KB ingestion batch.

## extraction_method

Example:

```text id="36sz36"
deterministic_parser_v1
```

## extraction_status

Allowed values:

* EXTRACTED
* PARTIAL
* FAILED

## normalization_status

Allowed values:

* NORMALIZED
* NEEDS_REVIEW

## review_status

Allowed values:

* AUTO_APPROVED
* HUMAN_REVIEWED
* REJECTED

## content_hash

Supports delta detection and idempotent updates.

---

# 9. UI Display Guidance

The primary user UI should display:

* headline
* plain_language_summary
* business_impact_summary
* technical_impact_summary
* recommended_action
* severity
* change_taxonomy
* kb_article_number
* kb_url

The primary user UI should not display by default:

* extraction_method
* normalization_status
* content_hash
* ingestion_run_id
* extraction_notes

These belong in an admin or audit drawer.

---

# 10. Deterministic Traceability Rule

Every displayed change must include:

* Oracle KB article number
* KB title
* source link

No user-facing finding may appear without source attribution.

---

# 11. Versioning Rule

All change records must include:

* stable `change_id`
* `schema_version`

Schema changes require explicit version increment.
