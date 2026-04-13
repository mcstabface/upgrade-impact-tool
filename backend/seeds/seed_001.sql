BEGIN;

-- customers
INSERT INTO customers (
  customer_id, customer_name, status, created_utc, updated_utc
) VALUES
  (1, 'Acme Health', 'ACTIVE', 1762732800, 1762732800)
ON CONFLICT (customer_id) DO NOTHING;

-- environments
INSERT INTO environments (
  environment_id, customer_id, environment_name, environment_type, status, created_utc, updated_utc
) VALUES
  (1, 1, 'Production', 'PROD', 'ACTIVE', 1762732800, 1762732800)
ON CONFLICT (environment_id) DO NOTHING;

-- snapshot
INSERT INTO customer_state_snapshots (
  snapshot_id, customer_id, environment_id, snapshot_version, snapshot_status,
  source_type, completeness_score, created_utc, created_by_user_id, content_hash, is_active
) VALUES
  (1, 1, 1, 1, 'ACTIVE', 'INTAKE', 0.92, 1762732800, 'seed', 'snapshot_hash_acme_prod_v1', TRUE)
ON CONFLICT (snapshot_id) DO NOTHING;

-- customer applications
INSERT INTO customer_applications (
  customer_application_id, snapshot_id, application_name, product_line,
  current_version, target_version, application_status
) VALUES
  (1, 1, 'Accounts Payable', 'ERP', '9.2.40', '9.2.41', 'IN_SCOPE'),
  (2, 1, 'Payroll', 'HCM', '9.2.40', '9.2.41', 'IN_SCOPE')
ON CONFLICT (customer_application_id) DO NOTHING;

-- modules
INSERT INTO customer_modules (
  customer_module_id, customer_application_id, module_name
) VALUES
  (1, 1, 'Invoice Processing'),
  (2, 1, 'Supplier Management'),
  (3, 2, 'Core Payroll'),
  (4, 2, 'Tax Reporting')
ON CONFLICT (customer_module_id) DO NOTHING;

-- kb articles
INSERT INTO kb_articles (
  kb_article_id, kb_article_number, kb_title, kb_url,
  product_line, application_name, published_date, current_status, created_utc, updated_utc
) VALUES
  (1, 'KB-2943812.1', 'Enhancements to Invoice Validation', 'https://example.com/kb/2943812-1', 'ERP', 'Accounts Payable', '2026-01-10', 'ACTIVE', 1762732800, 1762732800),
  (2, 'KB-3001120.1', 'Payroll Tax Calculation Update', 'https://example.com/kb/3001120-1', 'HCM', 'Payroll', '2026-01-12', 'ACTIVE', 1762732800, 1762732800),
  (3, 'KB-3001199.1', 'Workflow Approval UI Behavior Change', 'https://example.com/kb/3001199-1', 'ERP', 'Accounts Payable', '2026-01-15', 'ACTIVE', 1762732800, 1762732800)
ON CONFLICT (kb_article_id) DO NOTHING;

-- kb article versions
INSERT INTO kb_article_versions (
  kb_article_version_id, kb_article_id, source_hash, ingestion_run_id,
  parsed_status, normalization_status, extracted_utc, content_hash, is_current
) VALUES
  (1, 1, 'src_hash_kb_1_v1', 'seed_run_001', 'PARSED', 'NORMALIZED', 1762732800, 'content_hash_kb_1_v1', TRUE),
  (2, 2, 'src_hash_kb_2_v1', 'seed_run_001', 'PARSED', 'NORMALIZED', 1762732800, 'content_hash_kb_2_v1', TRUE),
  (3, 3, 'src_hash_kb_3_v1', 'seed_run_001', 'PARSED', 'NORMALIZED', 1762732800, 'content_hash_kb_3_v1', TRUE)
ON CONFLICT (kb_article_version_id) DO NOTHING;

-- change records
INSERT INTO change_records (
  change_id, schema_version, kb_article_id, kb_article_version_id,
  product_line, application_name, module_name, functional_area,
  version_from, version_to, change_taxonomy, severity, impact_type,
  headline, plain_language_summary, business_impact_summary, technical_impact_summary,
  recommended_action, user_confidence_note,
  standard_usage_assumed, customization_review_required, integration_review_required,
  extraction_status, normalization_status, review_status,
  created_utc, updated_utc, content_hash
) VALUES
  (
    1, 'v1', 1, 1,
    'ERP', 'Accounts Payable', 'Invoice Processing', 'Validation',
    '9.2.40', '9.2.41', 'CONFIGURATION', 'MEDIUM', 'FUNCTIONAL',
    'Invoice validation rule handling changed',
    'Invoice validation now applies additional matching logic for supplier attributes.',
    'Users may see invoices routed differently under standard validation settings.',
    'Validation rule evaluation order changed for supplier attribute checks.',
    'Review invoice validation configuration and regression test approval routing.',
    'Moderate confidence based on release notes and direct KB language.',
    TRUE, FALSE, FALSE,
    'COMPLETE', 'COMPLETE', 'APPROVED',
    1762732800, 1762732800, 'change_hash_1'
  ),
  (
    2, 'v1', 1, 1,
    'ERP', 'Accounts Payable', 'Supplier Management', 'Data Model',
    '9.2.40', '9.2.41', 'SCHEMA', 'HIGH', 'DATA',
    'Supplier attribute storage updated',
    'Supplier attribute persistence changed to support new validation controls.',
    'Existing supplier maintenance processes may require validation after upgrade.',
    'Underlying table structure and validation metadata handling changed.',
    'Validate supplier setup migration and compare seeded reference data.',
    'High confidence from KB schema notes.',
    TRUE, FALSE, TRUE,
    'COMPLETE', 'COMPLETE', 'APPROVED',
    1762732800, 1762732800, 'change_hash_2'
  ),
  (
    3, 'v1', 2, 2,
    'HCM', 'Payroll', 'Core Payroll', 'Tax Engine',
    '9.2.40', '9.2.41', 'BEHAVIORAL', 'HIGH', 'FUNCTIONAL',
    'Payroll tax rounding behavior updated',
    'Tax rounding logic has changed for specific withholding edge cases.',
    'Payroll totals may differ slightly and require reconciliation in validation.',
    'Rounding rule behavior was modified in the tax calculation pipeline.',
    'Run payroll parallel testing and reconcile sample employee populations.',
    'High confidence from vendor issue note and corrected behavior summary.',
    TRUE, FALSE, FALSE,
    'COMPLETE', 'COMPLETE', 'APPROVED',
    1762732800, 1762732800, 'change_hash_3'
  ),
  (
    4, 'v1', 2, 2,
    'HCM', 'Payroll', 'Tax Reporting', 'Integration',
    '9.2.40', '9.2.41', 'INTEGRATION', 'MEDIUM', 'INTEGRATION',
    'Outbound payroll tax interface payload changed',
    'Outbound tax reporting payload includes revised field formatting.',
    'Downstream tax reporting interfaces may require validation.',
    'Interface payload contract changed for selected tax fields.',
    'Review outbound interface mappings and test downstream consumers.',
    'Moderate confidence pending customer integration inventory.',
    TRUE, FALSE, TRUE,
    'COMPLETE', 'COMPLETE', 'APPROVED',
    1762732800, 1762732800, 'change_hash_4'
  ),
  (
    5, 'v1', 3, 3,
    'ERP', 'Accounts Payable', 'Invoice Processing', 'Workflow',
    '9.2.40', '9.2.41', 'WORKFLOW', 'MEDIUM', 'OPERATIONAL',
    'Approval workflow UI behavior changed',
    'Approval workflow screens display updated approval state indicators.',
    'Users may require minor retraining for approval screen changes.',
    'UI presentation and workflow status display behavior changed.',
    'Validate approval workflow with business users and update job aids.',
    'Moderate confidence from UI change note.',
    TRUE, TRUE, FALSE,
    'COMPLETE', 'COMPLETE', 'APPROVED',
    1762732800, 1762732800, 'change_hash_5'
  )
ON CONFLICT (change_id) DO NOTHING;

-- analysis run
INSERT INTO analysis_runs (
  analysis_id, customer_id, environment_id, snapshot_id,
  kb_catalog_version, analysis_status, overall_status,
  applies_count, review_required_count, unknown_count, blocked_count,
  assumptions_count, missing_inputs_count, derived_risks_count,
  started_utc, completed_utc, duration_ms, created_by_user_id
) VALUES
  (
    'analysis_seed_001', 1, 1, 1,
    'kb_seed_catalog_v1', 'REVIEW_REQUIRED', 'REVIEW_REQUIRED',
    2, 2, 1, 0,
    3, 2, 2,
    1762732810, 1762732875, 65000, 'seed'
  )
ON CONFLICT (analysis_id) DO NOTHING;

-- analysis applications
INSERT INTO analysis_applications (
  analysis_application_id, analysis_id, application_name,
  current_version, target_version, application_status,
  findings_count, review_required_count, blocked_count, unknown_count
) VALUES
  (1, 'analysis_seed_001', 'Accounts Payable', '9.2.40', '9.2.41', 'REVIEW_REQUIRED', 3, 1, 0, 0),
  (2, 'analysis_seed_001', 'Payroll', '9.2.40', '9.2.41', 'REVIEW_REQUIRED', 2, 1, 0, 1)
ON CONFLICT (analysis_application_id) DO NOTHING;

-- analysis findings
INSERT INTO analysis_findings (
  finding_id, analysis_id, analysis_application_id, change_id,
  finding_status, severity, change_taxonomy, impact_type,
  headline, plain_language_summary, business_impact_summary, technical_impact_summary,
  recommended_action, reason_for_status, assumptions_text, missing_inputs_text,
  requires_review, is_blocking, created_utc
) VALUES
  (
    1, 'analysis_seed_001', 1, 1,
    'APPLIES', 'MEDIUM', 'CONFIGURATION', 'FUNCTIONAL',
    'Invoice validation rule handling changed',
    'Accounts Payable invoice validation behavior is likely affected by the upgrade.',
    'Invoice processing users may experience different routing outcomes.',
    'Validation rule logic changed in a way that can affect configured behavior.',
    'Regression test invoice routing with current production scenarios.',
    'Current module usage matches KB scope.',
    'Standard application usage assumed.',
    'No custom workflow details provided.',
    FALSE, FALSE, 1762732880
  ),
  (
    2, 'analysis_seed_001', 1, 2,
    'REQUIRES_REVIEW', 'HIGH', 'SCHEMA', 'DATA',
    'Supplier attribute storage updated',
    'Supplier setup changes may affect configured integrations and data validation.',
    'Supplier onboarding and maintenance processes should be reviewed.',
    'Schema-related storage changes may affect custom downstream handling.',
    'Validate supplier data migration and integration touchpoints.',
    'Customer integration details were not fully provided.',
    'Standard application usage assumed.',
    'Integration inventory incomplete.',
    TRUE, FALSE, 1762732881
  ),
  (
    3, 'analysis_seed_001', 1, 5,
    'REQUIRES_REVIEW', 'MEDIUM', 'WORKFLOW', 'OPERATIONAL',
    'Approval workflow UI behavior changed',
    'Approval workflow screens have changed and may affect custom user procedures.',
    'Approval teams may need minor retraining.',
    'Workflow state display changed and may interact with custom approvals.',
    'Review approval workflow with business owners.',
    'Workflow customization risk detected.',
    'Standard workflow behavior assumed.',
    'Customization inventory incomplete.',
    TRUE, FALSE, 1762732882
  ),
  (
    4, 'analysis_seed_001', 2, 3,
    'APPLIES', 'HIGH', 'BEHAVIORAL', 'FUNCTIONAL',
    'Payroll tax rounding behavior updated',
    'Payroll tax calculation behavior is likely affected by the upgrade.',
    'Payroll validation may show differences that require reconciliation.',
    'Rounding logic changed in the payroll calculation path.',
    'Execute parallel payroll testing.',
    'Current payroll version is directly within KB scope.',
    'Standard payroll processing assumed.',
    NULL,
    FALSE, FALSE, 1762732883
  ),
  (
    5, 'analysis_seed_001', 2, 4,
    'UNKNOWN', 'MEDIUM', 'INTEGRATION', 'INTEGRATION',
    'Outbound payroll tax interface payload changed',
    'Potential interface impact cannot be confirmed without integration details.',
    'Downstream payroll reporting processes may be affected.',
    'Payload contract changed but customer-specific interface data is missing.',
    'Provide integration inventory and validate outbound consumers.',
    'Required customer integration context is missing.',
    'Standard outbound processing assumed.',
    'No payroll integration inventory provided.',
    FALSE, FALSE, 1762732884
  )
ON CONFLICT (finding_id) DO NOTHING;

-- finding evidence
INSERT INTO finding_evidence (
  finding_evidence_id, finding_id, kb_article_number, kb_title, kb_url,
  publication_date, evidence_excerpt, reference_section
) VALUES
  (
    1, 1, 'KB-2943812.1', 'Enhancements to Invoice Validation',
    'https://example.com/kb/2943812-1', '2026-01-10',
    'Invoice validation now evaluates additional supplier attributes before approval routing.',
    'Invoice Validation'
  ),
  (
    2, 2, 'KB-2943812.1', 'Enhancements to Invoice Validation',
    'https://example.com/kb/2943812-1', '2026-01-10',
    'Supplier attribute persistence has been updated to support revised validation controls.',
    'Supplier Attributes'
  ),
  (
    3, 3, 'KB-3001199.1', 'Workflow Approval UI Behavior Change',
    'https://example.com/kb/3001199-1', '2026-01-15',
    'Approval status indicators and workflow display states have changed in the updated UI.',
    'Workflow UI'
  ),
  (
    4, 4, 'KB-3001120.1', 'Payroll Tax Calculation Update',
    'https://example.com/kb/3001120-1', '2026-01-12',
    'Tax rounding behavior has been corrected for selected withholding edge cases.',
    'Tax Engine'
  ),
  (
    5, 5, 'KB-3001120.1', 'Payroll Tax Calculation Update',
    'https://example.com/kb/3001120-1', '2026-01-12',
    'Outbound tax reporting payload formatting has changed for revised tax field handling.',
    'Outbound Reporting'
  )
ON CONFLICT (finding_evidence_id) DO NOTHING;

-- state transitions
INSERT INTO state_transitions (
  state_transition_id, analysis_id, previous_state, new_state,
  trigger_event, user_id, transition_utc
) VALUES
  (1, 'analysis_seed_001', NULL, 'DRAFT', 'SEED_CREATE', 'seed', 1762732810),
  (2, 'analysis_seed_001', 'DRAFT', 'INTAKE_VALIDATED', 'INTAKE_VALIDATED', 'seed', 1762732820),
  (3, 'analysis_seed_001', 'INTAKE_VALIDATED', 'ANALYSIS_RUNNING', 'ANALYSIS_STARTED', 'seed', 1762732830),
  (4, 'analysis_seed_001', 'ANALYSIS_RUNNING', 'ANALYSIS_COMPLETE', 'ANALYSIS_FINISHED', 'seed', 1762732870),
  (5, 'analysis_seed_001', 'ANALYSIS_COMPLETE', 'REVIEW_REQUIRED', 'REVIEW_FLAGS_PRESENT', 'seed', 1762732875)
ON CONFLICT (state_transition_id) DO NOTHING;

COMMIT;