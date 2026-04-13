export type AnalysisStatus =
  | "DRAFT"
  | "INTAKE_VALIDATED"
  | "ANALYSIS_RUNNING"
  | "ANALYSIS_COMPLETE"
  | "REVIEW_REQUIRED"
  | "READY"
  | "ARCHIVED"
  | "BLOCKED"
  | "FAILED"
  | "STALE"
  | "REQUIRES_REFRESH";

export type FindingStatus =
  | "OPEN"
  | "REVIEW_REQUIRED"
  | "RESOLVED"
  | "ACCEPTED"
  | "REJECTED";

export type ReviewStatus =
  | "NOT_REQUIRED"
  | "PENDING"
  | "IN_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "COMPLETED";

export type ChangeTaxonomy =
  | "FEATURE_CHANGE"
  | "CONFIGURATION_CHANGE"
  | "SCHEMA_CHANGE"
  | "INTEGRATION_CHANGE"
  | "SECURITY_CHANGE"
  | "REPORTING_CHANGE"
  | "PROCESS_CHANGE"
  | "DEPRECATION"
  | "BUG_FIX"
  | "OTHER";

export type Severity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type ImpactType =
  | "NONE"
  | "FUNCTIONAL"
  | "TECHNICAL"
  | "OPERATIONAL"
  | "DATA"
  | "SECURITY"
  | "COMPLIANCE"
  | "PERFORMANCE"
  | "INTEGRATION";

export type EnvironmentType = "DEV" | "TEST" | "PROD";

export interface EnumCatalogResponse {
  analysis_statuses: AnalysisStatus[];
  finding_statuses: FindingStatus[];
  review_statuses: ReviewStatus[];
  change_taxonomies: ChangeTaxonomy[];
  severities: Severity[];
  impact_types: ImpactType[];
  environment_types: EnvironmentType[];
}