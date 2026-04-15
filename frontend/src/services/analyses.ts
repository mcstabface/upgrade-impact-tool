import { apiGet, apiPost } from "./api";

export type AnalysisStatusResponse = {
  analysis_id: string;
  status: string;
  progress_pct: number;
  current_stage: string;
};

export type AnalysisStalenessResponse = {
  analysis_id: string;
  status: string;
  is_stale: boolean;
  triggers: string[];
  stale_detected_utc: number | null;
  recorded_snapshot_hash: string | null;
  current_snapshot_hash: string | null;
  recorded_kb_catalog_hash: string | null;
  current_kb_catalog_hash: string;
  recorded_analysis_input_hash: string | null;
  current_analysis_input_hash: string;
};

export type AnalysisRefreshResponse = {
  previous_analysis_id: string;
  new_analysis_id: string;
  status: string;
  started_utc: number;
  snapshot_id: number;
  snapshot_hash: string;
  kb_catalog_hash: string;
  analysis_input_hash: string;
};

export type AnalysisOverviewResponse = {
  analysis_id: string;
  customer_name: string;
  environment_name: string;
  analysis_date: number | null;
  overall_status: string;
  summary: {
    applies_count: number;
    review_required_count: number;
    unknown_count: number;
    blocked_count: number;
  };
  assumptions: string[];
  missing_inputs: string[];
  derived_risks: string[];
  started_utc: number | null;
  completed_utc: number | null;
  duration_ms: number | null;
  stale_reason: string | null;
  stale_detected_utc: number | null;
  previous_analysis_id: string | null;
  top_risks: string[];
  top_actions: string[];
  applications: {
    analysis_application_id: number;
    application_name: string;
    current_version: string;
    target_version: string;
    status: string;
    findings_count: number;
  }[];
};

export type AnalysisApplicationDetailResponse = {
  analysis_application_id: number;
  application_name: string;
  current_version: string;
  target_version: string;
  application_status: string;
  findings: {
    finding_id: number;
    status: string;
    severity: string;
    change_taxonomy: string;
    headline: string;
    recommended_action: string | null;
    kb_reference: string;
  }[];
};

export function getAnalysisStatus(id: string) {
  return apiGet<AnalysisStatusResponse>(`/analyses/${id}/status`);
}

export function getAnalysisOverview(id: string) {
  return apiGet<AnalysisOverviewResponse>(`/analyses/${id}`);
}

export function evaluateAnalysisStaleness(id: string) {
  return apiPost<AnalysisStalenessResponse, Record<string, never>>(
    `/analyses/${id}/evaluate-staleness`,
    {},
  );
}

export function refreshAnalysis(id: string) {
  return apiPost<AnalysisRefreshResponse, Record<string, never>>(
    `/analyses/${id}/refresh`,
    {},
  );
}

export function getAnalysisApplicationDetail(id: string, applicationId: string) {
  return apiGet<AnalysisApplicationDetailResponse>(
    `/analyses/${id}/applications/${applicationId}`,
  );
}