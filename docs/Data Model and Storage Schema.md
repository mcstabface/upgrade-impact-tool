Data Model and Storage Schema v1

System: Upgrade Impact Analysis Tool
Purpose: Define the persistent storage model for intake, KB normalization, analysis runs, findings, review workflow, and audit traceability
Design Goal: Single durable truth for engine, UI, and governance

1. Storage Design Principles

The storage model must support:

deterministic re-runs
historical baselines
delta-based refresh
explicit provenance
UI-friendly retrieval
admin/audit inspection
no destructive overwrites of prior truth

Core rule:

New state creates new records.
Prior state remains inspectable.

That is non-negotiable if you want trust.

2. Storage Domains

The system naturally separates into seven domains:

1. Customer and Environment
2. Intake Baselines
3. Vendor KB Catalog
4. Normalized Change Records
5. Analysis Runs
6. Findings and Review Workflow
7. Audit / State Transitions
3. Entity Overview

High-level entities:

customers
environments
customer_state_snapshots
customer_applications
customer_modules
customer_customizations
customer_integrations
kb_articles
kb_article_versions
change_records
analysis_runs
analysis_applications
analysis_findings
finding_evidence
review_items
state_transitions
exports
DOMAIN 1 — CUSTOMER AND ENVIRONMENT
4. customers

Purpose:

Store customer identity once.

Fields
customers:
  customer_id: PK
  customer_name:
  status:
  created_utc:
  updated_utc:
Notes
one row per customer
referenced by all downstream entities
5. environments

Purpose:

Represent customer environments separately.

Fields
environments:
  environment_id: PK
  customer_id: FK -> customers.customer_id
  environment_name:
  environment_type:
  status:
  created_utc:
  updated_utc:
Notes

Environment type examples:

DEV
TEST
PROD

This matters because one customer may have multiple upgrade tracks.

DOMAIN 2 — CUSTOMER STATE SNAPSHOTS
6. customer_state_snapshots

Purpose:

Immutable baseline or delta state for a customer environment.

Fields
customer_state_snapshots:
  snapshot_id: PK
  customer_id: FK
  environment_id: FK
  snapshot_version:
  snapshot_status:
  source_type:
  completeness_score:
  created_utc:
  created_by_user_id:
  content_hash:
  is_active:
Notes
one snapshot per intake submission
supports historical comparison
content_hash enables idempotent delta detection
is_active points to current truth without deleting history
7. customer_applications

Purpose:

Applications included in a specific snapshot.

Fields
customer_applications:
  customer_application_id: PK
  snapshot_id: FK -> customer_state_snapshots.snapshot_id
  application_name:
  product_line:
  current_version:
  target_version:
  application_status:
8. customer_modules

Purpose:

Enabled modules for a customer application.

Fields
customer_modules:
  customer_module_id: PK
  customer_application_id: FK -> customer_applications.customer_application_id
  module_name:
9. customer_customizations

Purpose:

Store declared customizations.

Fields
customer_customizations:
  customization_id: PK
  customer_application_id: FK
  object_name:
  object_type:
  description:
  owning_team:
  criticality:
10. customer_integrations

Purpose:

Store declared integrations.

Fields
customer_integrations:
  integration_id: PK
  customer_application_id: FK
  integration_name:
  source_system:
  target_system:
  interface_type:
  endpoint_or_job_name:
  schedule:
  criticality:
11. customer_jobs

Purpose:

Store reports, batch jobs, scheduled tasks.

Fields
customer_jobs:
  job_id: PK
  customer_application_id: FK
  job_name:
  job_type:
  schedule:
  owner:
  description:
DOMAIN 3 — VENDOR KB CATALOG
12. kb_articles

Purpose:

Store Oracle KB identity.

Fields
kb_articles:
  kb_article_id: PK
  kb_article_number:
  kb_title:
  kb_url:
  product_line:
  application_name:
  published_date:
  current_status:
  created_utc:
  updated_utc:
Notes

This is the canonical KB identity table.

13. kb_article_versions

Purpose:

Track changes to KB content over time.

Fields
kb_article_versions:
  kb_article_version_id: PK
  kb_article_id: FK -> kb_articles.kb_article_id
  source_hash:
  ingestion_run_id:
  parsed_status:
  normalization_status:
  extracted_utc:
  content_hash:
  is_current:
Notes

This table supports:

KB delta detection
historical replay
re-normalization after parser improvements
DOMAIN 4 — NORMALIZED CHANGE RECORDS
14. change_records

Purpose:

Persistent normalized changes derived from KBs.

This is the core comparison object.

Fields
change_records:
  change_id: PK
  schema_version:
  kb_article_id: FK -> kb_articles.kb_article_id
  kb_article_version_id: FK -> kb_article_versions.kb_article_version_id

  product_line:
  application_name:
  module_name:
  functional_area:

  version_from:
  version_to:

  change_taxonomy:
  severity:
  impact_type:

  headline:
  plain_language_summary:
  business_impact_summary:
  technical_impact_summary:
  recommended_action:
  user_confidence_note:

  standard_usage_assumed:
  customization_review_required:
  integration_review_required:

  extraction_status:
  normalization_status:
  review_status:

  created_utc:
  updated_utc:
  content_hash:
Notes

This is intentionally dual-purpose:

engine-readable
UI-displayable
15. change_record_objects

Purpose:

Affected technical objects for a change record.

Fields
change_record_objects:
  change_record_object_id: PK
  change_id: FK -> change_records.change_id
  object_name:
  object_type:
16. change_record_features

Purpose:

Affected functional features.

Fields
change_record_features:
  change_record_feature_id: PK
  change_id: FK
  feature_name:
17. change_record_integrations

Purpose:

Affected interface surfaces.

Fields
change_record_integrations:
  change_record_integration_id: PK
  change_id: FK
  integration_surface:
18. change_record_evidence

Purpose:

Store evidence excerpts for traceability and UI trust.

Fields
change_record_evidence:
  evidence_id: PK
  change_id: FK -> change_records.change_id
  quoted_reference_text:
  reference_section:
  extraction_notes:
Notes

Every user-facing finding should ultimately point back here via KB provenance. That matches the requirement that visible claims remain source-backed and inspectable.

DOMAIN 5 — ANALYSIS RUNS
19. analysis_runs

Purpose:

Represent one execution of upgrade analysis.

Fields
analysis_runs:
  analysis_id: PK
  customer_id: FK
  environment_id: FK
  snapshot_id: FK -> customer_state_snapshots.snapshot_id

  kb_catalog_version:
  analysis_status:
  overall_status:

  applies_count:
  review_required_count:
  unknown_count:
  blocked_count:

  assumptions_count:
  missing_inputs_count:
  derived_risks_count:

  started_utc:
  completed_utc:
  duration_ms:
  created_by_user_id:
Notes

This is the parent object for the report.

20. analysis_applications

Purpose:

Per-application status within an analysis.

Fields
analysis_applications:
  analysis_application_id: PK
  analysis_id: FK -> analysis_runs.analysis_id
  application_name:
  current_version:
  target_version:
  application_status:
  findings_count:
  review_required_count:
  blocked_count:
  unknown_count:
DOMAIN 6 — FINDINGS AND REVIEW WORKFLOW
21. analysis_findings

Purpose:

Resolved analysis result for a specific change record against a specific customer/application context.

Fields
analysis_findings:
  finding_id: PK
  analysis_id: FK -> analysis_runs.analysis_id
  analysis_application_id: FK -> analysis_applications.analysis_application_id
  change_id: FK -> change_records.change_id

  finding_status:
  severity:
  change_taxonomy:
  impact_type:

  headline:
  plain_language_summary:
  business_impact_summary:
  technical_impact_summary:
  recommended_action:

  reason_for_status:
  assumptions_text:
  missing_inputs_text:

  requires_review:
  is_blocking:

  created_utc:
Notes

This is the direct backbone for:

Results Overview
Application Detail
Finding Detail
Review Queue
22. finding_evidence

Purpose:

Evidence displayed with a finding.

Fields
finding_evidence:
  finding_evidence_id: PK
  finding_id: FK -> analysis_findings.finding_id
  kb_article_number:
  kb_title:
  kb_url:
  publication_date:
  evidence_excerpt:
  reference_section:
Notes

This denormalizes user-facing evidence for fast UI retrieval and export stability.

23. review_items

Purpose:

Track manual review workflow.

Fields
review_items:
  review_item_id: PK
  finding_id: FK -> analysis_findings.finding_id
  review_reason:
  review_status:
  assigned_owner_user_id:
  due_date_utc:
  comments_count:
  created_utc:
  resolved_utc:
Review status values
OPEN
IN_PROGRESS
RESOLVED
DEFERRED
24. review_comments

Purpose:

Store collaboration history.

Fields
review_comments:
  review_comment_id: PK
  review_item_id: FK -> review_items.review_item_id
  user_id:
  comment_text:
  created_utc:
DOMAIN 7 — AUDIT / STATE TRANSITIONS
25. state_transitions

Purpose:

Track lifecycle transitions for each analysis.

Fields
state_transitions:
  state_transition_id: PK
  analysis_id: FK -> analysis_runs.analysis_id
  previous_state:
  new_state:
  trigger_event:
  user_id:
  transition_utc:
Notes

This supports deterministic replay of workflow movement.

26. exports

Purpose:

Track report exports without mutating analysis truth.

Fields
exports:
  export_id: PK
  analysis_id: FK -> analysis_runs.analysis_id
  export_type:
  export_scope:
  generated_by_user_id:
  generated_utc:
  file_path:
  content_hash:
27. notifications

Purpose:

Track emitted notifications.

Fields
notifications:
  notification_id: PK
  analysis_id: FK
  notification_type:
  channel:
  recipient:
  sent_utc:
  delivery_status:
RELATIONSHIP MODEL
28. Core Relationships
customers
  └── environments
        └── customer_state_snapshots
              └── customer_applications
                    ├── customer_modules
                    ├── customer_customizations
                    ├── customer_integrations
                    └── customer_jobs

kb_articles
  └── kb_article_versions
        └── change_records
              ├── change_record_objects
              ├── change_record_features
              ├── change_record_integrations
              └── change_record_evidence

analysis_runs
  ├── analysis_applications
  │     └── analysis_findings
  │            ├── finding_evidence
  │            └── review_items
  │                  └── review_comments
  ├── state_transitions
  ├── exports
  └── notifications
KEY DESIGN CHOICES
29. Why snapshots are immutable

Because customer state changes over time, and we need to know:

what did we know when this analysis was run?

Mutable baselines destroy that.

30. Why findings are persisted separately from change records

Because a change record is vendor truth, while a finding is:

vendor change
matched against
customer context
at a specific point in time

Those are not the same thing.

31. Why evidence is denormalized into finding_evidence

Because exports and UI rendering should not depend on joining back through a shifting KB normalization layer every time. Stable visible truth matters more than perfect relational asceticism.

32. Why admin fields stay out of primary finding tables where possible

Because user-facing UX should not have to sift through ingestion mechanics. The UI strategy we defined depends on progressive disclosure and a clean primary experience, with deeper details available when needed.

INDEXING RECOMMENDATIONS
33. Required indexes
kb_articles
UNIQUE(kb_article_number)
INDEX(application_name, published_date)
kb_article_versions
INDEX(kb_article_id, is_current)
INDEX(source_hash)
customer_state_snapshots
INDEX(customer_id, environment_id, is_active)
INDEX(content_hash)
customer_applications
INDEX(snapshot_id, application_name)
change_records
INDEX(application_name, module_name, version_from, version_to)
INDEX(change_taxonomy)
INDEX(severity)
INDEX(kb_article_id)
analysis_runs
INDEX(customer_id, environment_id, completed_utc)
INDEX(snapshot_id)
INDEX(overall_status)
analysis_findings
INDEX(analysis_id, finding_status)
INDEX(analysis_application_id, severity)
INDEX(change_id)
INDEX(requires_review, is_blocking)
review_items
INDEX(review_status, assigned_owner_user_id)
INDEX(finding_id)
DELTA DETECTION SUPPORT
34. KB delta detection

Use:

kb_article_number + source_hash

Logic:

same KB number + new hash = new KB version
35. Customer state delta detection

Use:

customer_id + environment_id + content_hash

Logic:

same customer/environment + new hash = new snapshot version
36. Re-analysis trigger table

Optional but useful in v1.1:

refresh_triggers:
  refresh_trigger_id: PK
  analysis_id: FK
  trigger_type:
  source_domain:
  source_record_id:
  detected_utc:
  processed_utc:
  trigger_status:

This would make stale/refresh handling easier later.

UI QUERY SUPPORT
37. Primary UI views this model supports directly
Dashboard
analysis_runs
aggregated analysis_findings
top review_items
Results Overview
analysis_runs
analysis_applications
analysis_findings
Application Detail
analysis_applications
analysis_findings
Finding Detail
analysis_findings
finding_evidence
review_items
Review Queue
review_items
analysis_findings
finding_evidence
Admin screens
kb_articles
kb_article_versions
customer_state_snapshots
state_transitions
STATUS ENUMS TO LOCK DOWN
38. analysis_status
DRAFT
INTAKE_VALIDATED
ANALYSIS_RUNNING
ANALYSIS_COMPLETE
REVIEW_REQUIRED
READY
BLOCKED
FAILED
STALE
ARCHIVED
39. finding_status
APPLIES
DOES_NOT_APPLY
POSSIBLE_MATCH
UNKNOWN
BLOCKED
REQUIRES_REVIEW
40. review_status
OPEN
IN_PROGRESS
RESOLVED
DEFERRED
MVP TABLE PRIORITY
41. Build first

If we want smallest safe implementation order:

Tier 1
customers
environments
customer_state_snapshots
customer_applications
customer_modules
kb_articles
kb_article_versions
change_records
analysis_runs
analysis_applications
analysis_findings
finding_evidence
state_transitions
Tier 2
customer_customizations
customer_integrations
customer_jobs
review_items
review_comments
exports
Tier 3
notifications
refresh_triggers

That gets the core product working before we add all the nice pain.