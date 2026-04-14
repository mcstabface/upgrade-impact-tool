import { apiGet } from "./api";

export type AnalysisStatusResponse = {
  analysis_id: string;
  status: string;
  progress_pct: number;
  current_stage: string;
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

export function getAnalysisApplicationDetail(id: string, applicationId: string) {
  return apiGet<AnalysisApplicationDetailResponse>(
    `/analyses/${id}/applications/${applicationId}`,
  );
}