import { apiGet, apiPatch, apiPost } from "./api";

export type IntakeCreateRequest = {
  customer_name: string;
  environment_name: string;
  environment_type: "DEV" | "TEST" | "PROD";
};

export type IntakeCreateResponse = {
  intake_id: string;
  status: string;
  created_utc: number;
};

export type IntakeDetailResponse = {
  intake_id: string;
  status: string;
  customer_name: string;
  environment_name: string;
  environment_type: string;
  applications: unknown[];
};

export type IntakeUpdateRequest = {
  applications?: {
    application_name: string;
    product_line: string;
    current_version: string;
    target_version: string;
    modules_enabled: string[];
  }[];
  primary_technical_contact?: {
    name: string;
    email?: string | null;
  };
  primary_business_contact?: {
    name: string;
    email?: string | null;
  };
  environment_count?: number;
  environment_classification?: string[];
  upgrade_sequence?: string[];
  vendor_kb_documents?: {
    article_number: string;
    title: string;
    publication_date: string;
    source_link: string;
  }[];
};

export type IntakeValidateResponse = {
  intake_id: string;
  status: string;
  completeness_score: number;
  missing_required_fields: string[];
  warnings: string[];
};

export type StartAnalysisResponse = {
  analysis_id: string;
  status: string;
  started_utc: number;
};

export function createIntake(
  payload: IntakeCreateRequest,
): Promise<IntakeCreateResponse> {
  return apiPost<IntakeCreateResponse, IntakeCreateRequest>("/intakes", payload);
}

export function getIntake(id: string): Promise<IntakeDetailResponse> {
  return apiGet<IntakeDetailResponse>(`/intakes/${id}`);
}

export function updateIntake(id: string, payload: IntakeUpdateRequest) {
  return apiPatch(`/intakes/${id}`, payload);
}

export function validateIntake(id: string): Promise<IntakeValidateResponse> {
  return apiPost<IntakeValidateResponse, Record<string, never>>(
    `/intakes/${id}/validate`,
    {},
  );
}

export function startAnalysis(id: string): Promise<StartAnalysisResponse> {
  return apiPost<StartAnalysisResponse, { run_mode: string }>(
    `/intakes/${id}/analyses`,
    { run_mode: "STANDARD" },
  );
}