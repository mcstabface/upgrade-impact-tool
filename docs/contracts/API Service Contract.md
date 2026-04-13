API / Service Contract v1

System: Upgrade Impact Analysis Tool
Purpose: Define implementation-facing service endpoints for intake, analysis execution, results retrieval, review workflow, export, and refresh
Design Goal: Support a user-friendly frontend, deterministic execution, and full traceability

1. API Design Principles

The service layer must support:

guided user workflow
deterministic execution
stable IDs for UI navigation
evidence-backed retrieval
explicit status transitions
immutable historical runs

Core rules:

No silent mutation of completed analysis results
No hidden refreshes
No unsupported finding without KB provenance

This is not a “smart” API.
It is a controlled workflow surface.

2. API Domains

The contract is organized into these service groups:

1. Intake
2. Analysis
3. Dashboard / Results Retrieval
4. Findings / Evidence
5. Review Workflow
6. Export
7. Refresh / Delta
8. Admin
DOMAIN 1 — INTAKE
3. Create Intake Draft
Endpoint
POST /api/v1/intakes
Purpose

Create a new intake draft for a customer/environment.

Request
{
  "customer_name": "Acme Health",
  "environment_name": "Production",
  "environment_type": "PROD"
}
Response
{
  "intake_id": "intk_001",
  "status": "DRAFT",
  "created_utc": 1775990400
}
4. Update Intake Draft
Endpoint
PATCH /api/v1/intakes/{intake_id}
Purpose

Update sections of a draft intake.

Request
{
  "applications": [
    {
      "application_name": "Accounts Payable",
      "product_line": "PeopleSoft",
      "current_version": "9.2.38",
      "target_version": "9.2.39",
      "modules_enabled": ["Invoice Processing", "Payment Scheduling"]
    }
  ]
}
Response
{
  "intake_id": "intk_001",
  "status": "DRAFT",
  "completeness_score": 64
}
5. Upload Intake File
Endpoint
POST /api/v1/intakes/{intake_id}/upload
Purpose

Upload structured intake input.

Supported Formats
CSV
XLSX
JSON
Response
{
  "intake_id": "intk_001",
  "upload_status": "ACCEPTED",
  "parsed_status": "IN_PROGRESS"
}
6. Validate Intake
Endpoint
POST /api/v1/intakes/{intake_id}/validate
Purpose

Check required data completeness and structure before analysis.

Response — Success
{
  "intake_id": "intk_001",
  "status": "INTAKE_VALIDATED",
  "completeness_score": 82,
  "missing_required_fields": [],
  "warnings": [
    "No integration inventory provided",
    "No customization inventory provided"
  ]
}
Response — Blocked
{
  "intake_id": "intk_001",
  "status": "BLOCKED",
  "missing_required_fields": [
    "target_version",
    "modules_enabled"
  ]
}
7. Get Intake Detail
Endpoint
GET /api/v1/intakes/{intake_id}
Purpose

Retrieve the full current intake draft or validated intake.

Response
{
  "intake_id": "intk_001",
  "status": "DRAFT",
  "customer_name": "Acme Health",
  "environment_name": "Production",
  "environment_type": "PROD",
  "applications": []
}
DOMAIN 2 — ANALYSIS
8. Start Analysis
Endpoint
POST /api/v1/intakes/{intake_id}/analyses
Purpose

Begin upgrade impact analysis from a validated intake.

Request
{
  "run_mode": "STANDARD"
}
Response
{
  "analysis_id": "anl_001",
  "status": "ANALYSIS_RUNNING",
  "started_utc": 1775990452
}
9. Get Analysis Status
Endpoint
GET /api/v1/analyses/{analysis_id}/status
Purpose

Return live workflow state and progress.

Response
{
  "analysis_id": "anl_001",
  "status": "ANALYSIS_RUNNING",
  "progress_pct": 68,
  "current_stage": "MATCHING_CHANGE_RECORDS"
}
10. Cancel Analysis
Endpoint
POST /api/v1/analyses/{analysis_id}/cancel
Purpose

Cancel a running analysis.

Response
{
  "analysis_id": "anl_001",
  "status": "FAILED",
  "reason": "Cancelled by user"
}
DOMAIN 3 — DASHBOARD / RESULTS RETRIEVAL
11. Get Dashboard
Endpoint
GET /api/v1/dashboard
Purpose

Return top-level user landing page data.

Query Parameters
customer_id (optional)
environment_id (optional)
status (optional)
Response
{
  "analyses": [
    {
      "analysis_id": "anl_001",
      "customer_name": "Acme Health",
      "environment_name": "Production",
      "analysis_date": 1775990501,
      "overall_status": "REVIEW_REQUIRED",
      "applications_count": 3,
      "applies_count": 14,
      "review_required_count": 5,
      "unknown_count": 3,
      "blocked_count": 2
    }
  ]
}
12. Get Analysis Results Overview
Endpoint
GET /api/v1/analyses/{analysis_id}
Purpose

Return report overview screen data.

Response
{
  "analysis_id": "anl_001",
  "customer_name": "Acme Health",
  "environment_name": "Production",
  "analysis_date": 1775990501,
  "overall_status": "REVIEW_REQUIRED",
  "summary": {
    "applies_count": 14,
    "review_required_count": 5,
    "unknown_count": 3,
    "blocked_count": 2
  },
  "assumptions": [
    "Standard application usage assumed"
  ],
  "missing_inputs": [
    "No integration inventory provided for Payroll"
  ],
  "derived_risks": [
    "Technical interface impact may be understated"
  ],
  "applications": [
    {
      "analysis_application_id": "aa_001",
      "application_name": "Accounts Payable",
      "current_version": "9.2.38",
      "target_version": "9.2.39",
      "status": "REVIEW_REQUIRED",
      "findings_count": 6
    }
  ]
}
13. Get Application Detail
Endpoint
GET /api/v1/analyses/{analysis_id}/applications/{analysis_application_id}
Purpose

Return all findings for one application.

Query Parameters
status
severity
taxonomy
review_required
view_mode=business|technical
Response
{
  "analysis_application_id": "aa_001",
  "application_name": "Accounts Payable",
  "current_version": "9.2.38",
  "target_version": "9.2.39",
  "application_status": "REVIEW_REQUIRED",
  "findings": [
    {
      "finding_id": "f_001",
      "status": "APPLIES",
      "severity": "MEDIUM",
      "change_taxonomy": "BEHAVIORAL",
      "headline": "Invoice validation behavior updated",
      "recommended_action": "Review validation workflow",
      "kb_reference": "KB 2943812.1"
    }
  ]
}
DOMAIN 4 — FINDINGS / EVIDENCE
14. Get Finding Detail
Endpoint
GET /api/v1/findings/{finding_id}
Purpose

Return the full finding detail screen.

Response
{
  "finding_id": "f_001",
  "status": "APPLIES",
  "severity": "MEDIUM",
  "change_taxonomy": "BEHAVIORAL",
  "application_name": "Accounts Payable",
  "module_name": "Invoice Processing",
  "version_range": {
    "from": "9.2.38",
    "to": "9.2.39"
  },
  "headline": "Invoice validation behavior updated",
  "plain_language_summary": "Oracle changed duplicate invoice validation behavior.",
  "business_impact_summary": "This may affect invoice approval workflows.",
  "technical_impact_summary": "Custom validation scripts should be reviewed.",
  "recommended_action": "Test invoice validation before upgrade.",
  "assumptions": [
    "Standard usage assumed"
  ],
  "missing_inputs": [
    "No customization list provided"
  ],
  "reason_for_status": "Matched application version and enabled module",
  "evidence": {
    "kb_article_number": "2943812.1",
    "kb_title": "Enhancements to Invoice Validation",
    "kb_url": "https://support.oracle.com/...",
    "publication_date": "2026-03-14",
    "evidence_excerpt": "Duplicate invoice detection has been enhanced..."
  },
  "technical_details": {
    "affected_objects": [
      { "object_name": "AP_INVOICE", "object_type": "table" }
    ],
    "affected_features": [
      "duplicate invoice detection"
    ],
    "affected_integrations": [
      "invoice create API"
    ]
  }
}
15. Search Findings
Endpoint
GET /api/v1/findings/search
Purpose

Support cross-analysis search/filter in UI.

Query Parameters
q
application_name
kb_article_number
status
severity
taxonomy
requires_review
Response
{
  "results": [
    {
      "finding_id": "f_001",
      "headline": "Invoice validation behavior updated",
      "application_name": "Accounts Payable",
      "kb_article_number": "2943812.1",
      "status": "APPLIES"
    }
  ]
}
DOMAIN 5 — REVIEW WORKFLOW
16. Create Review Item
Endpoint
POST /api/v1/findings/{finding_id}/review-items
Purpose

Create a review task from a finding.

Request
{
  "review_reason": "Customization detected",
  "assigned_owner_user_id": "usr_014",
  "due_date_utc": 1776508800
}
Response
{
  "review_item_id": "rvw_001",
  "review_status": "OPEN"
}
17. Get Review Queue
Endpoint
GET /api/v1/review-items
Purpose

Return the review queue screen.

Query Parameters
owner_user_id
application_name
review_status
is_blocking
Response
{
  "items": [
    {
      "review_item_id": "rvw_001",
      "finding_id": "f_001",
      "application_name": "Accounts Payable",
      "headline": "Invoice validation behavior updated",
      "review_reason": "Customization detected",
      "review_status": "OPEN",
      "assigned_owner_user_id": "usr_014",
      "kb_article_number": "2943812.1"
    }
  ]
}
18. Update Review Item
Endpoint
PATCH /api/v1/review-items/{review_item_id}
Purpose

Assign owner, change status, or update due date.

Request
{
  "review_status": "IN_PROGRESS",
  "assigned_owner_user_id": "usr_021"
}
Response
{
  "review_item_id": "rvw_001",
  "review_status": "IN_PROGRESS"
}
19. Add Review Comment
Endpoint
POST /api/v1/review-items/{review_item_id}/comments
Request
{
  "comment_text": "Need validation from AP dev team."
}
Response
{
  "review_comment_id": "rvc_001",
  "created_utc": 1775990650
}
DOMAIN 6 — EXPORT
20. Export Full Report
Endpoint
POST /api/v1/analyses/{analysis_id}/exports
Purpose

Generate export without mutating report truth.

Request
{
  "export_type": "PDF",
  "export_scope": "FULL_REPORT"
}
Response
{
  "export_id": "exp_001",
  "export_type": "PDF",
  "status": "GENERATED",
  "file_url": "/downloads/exp_001.pdf"
}
21. Export Application Report
Endpoint
POST /api/v1/analyses/{analysis_id}/applications/{analysis_application_id}/exports
Request
{
  "export_type": "PDF"
}
22. Export Review Queue
Endpoint
POST /api/v1/review-items/exports
Request
{
  "export_type": "CSV",
  "filters": {
    "review_status": "OPEN"
  }
}
DOMAIN 7 — REFRESH / DELTA
23. Get Refresh Status
Endpoint
GET /api/v1/analyses/{analysis_id}/refresh-status
Purpose

Show whether analysis is current, stale, or requires refresh.

Response
{
  "analysis_id": "anl_001",
  "refresh_status": "STALE",
  "trigger_summary": [
    "New KB version detected for Accounts Payable",
    "Customer baseline updated for Payroll"
  ]
}
24. Run Refresh
Endpoint
POST /api/v1/analyses/{analysis_id}/refresh
Purpose

Re-run analysis using latest KB/customer deltas.

Response
{
  "analysis_id": "anl_001",
  "new_analysis_id": "anl_002",
  "status": "ANALYSIS_RUNNING"
}
Note

Refresh should create a new analysis run, not overwrite the prior one.
That preserves history and keeps the state model honest.

25. Get Delta Summary
Endpoint
GET /api/v1/analyses/{analysis_id}/delta-summary
Purpose

Show what changed since last analysis.

Response
{
  "analysis_id": "anl_001",
  "delta_summary": {
    "new_kb_articles": 2,
    "updated_kb_articles": 1,
    "customer_snapshot_changed": true,
    "applications_impacted": [
      "Accounts Payable",
      "Payroll"
    ]
  }
}
DOMAIN 8 — ADMIN
26. Get KB Catalog Status
Endpoint
GET /api/v1/admin/kb-catalog
Purpose

Return admin view of KB ingestion and normalization state.

Response
{
  "kb_articles_total": 402,
  "kb_articles_current": 394,
  "normalization_failed": 8,
  "last_ingestion_utc": 1775989000
}
27. Trigger KB Ingestion
Endpoint
POST /api/v1/admin/kb-catalog/ingest
Purpose

Trigger KB ingestion batch.

Request
{
  "source_batch_name": "oracle_kb_apr_2026"
}
28. Get Customer Snapshot Admin View
Endpoint
GET /api/v1/admin/customer-snapshots/{snapshot_id}
Purpose

Return detailed current-state baseline for admin inspection.

29. Get Audit Trail
Endpoint
GET /api/v1/admin/analyses/{analysis_id}/audit
Purpose

Return state transitions, trace IDs, export history, and provenance.

Response
{
  "analysis_id": "anl_001",
  "state_transitions": [
    {
      "previous_state": "DRAFT",
      "new_state": "INTAKE_VALIDATED",
      "trigger_event": "validate_intake",
      "timestamp": 1775990412
    }
  ]
}
RESPONSE STANDARDS
30. Standard Error Envelope

All errors should return:

{
  "error_code": "INTAKE_REQUIRED_FIELD_MISSING",
  "message": "Target version is required.",
  "details": {
    "field": "target_version"
  }
}
31. Standard Status Enum Values
Analysis status
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
Finding status
APPLIES
DOES_NOT_APPLY
POSSIBLE_MATCH
UNKNOWN
BLOCKED
REQUIRES_REVIEW
Review status
OPEN
IN_PROGRESS
RESOLVED
DEFERRED
UI-BACKEND ALIGNMENT RULES
32. Business vs Technical View

The API should support both views over the same truth.

That can be done either by:

a view_mode query parameter
or
returning all data and letting UI control disclosure

For v1, I would return all necessary data and let the UI decide what to expand. That keeps the contract simpler.

33. KB Provenance Rule

No finding detail response may be returned without KB source attribution.
That is essential for trust and matches the requirement that user-visible claims remain source-backed.

34. Refresh Rule

Refresh must always create:

a new analysis_id

Never overwrite prior analysis output.

This is consistent with the immutability and replayability principles in the architecture.

MVP ENDPOINT PRIORITY
35. Build first
Tier 1
Create Intake
Update Intake
Validate Intake
Start Analysis
Get Analysis Status
Get Dashboard
Get Analysis Results Overview
Get Application Detail
Get Finding Detail
Tier 2
Create Review Item
Get Review Queue
Update Review Item
Export Full Report
Tier 3
Refresh Status
Run Refresh
Delta Summary
Admin endpoints