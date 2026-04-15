import { apiGet, apiPost } from "./api";

export type FindingDetailResponse = {
  finding_id: number;
  status: string;
  severity: string;
  change_taxonomy: string;
  application_name: string;
  module_name: string | null;
  version_range: {
    from_version: string | null;
    to_version: string | null;
  };
  headline: string;
  plain_language_summary: string;
  business_impact_summary: string | null;
  technical_impact_summary: string | null;
  recommended_action: string | null;
  assumptions: string[];
  missing_inputs: string[];
  reason_for_status: string | null;
  evidence: {
    kb_article_number: string;
    kb_title: string;
    kb_url: string;
    publication_date: string;
    evidence_excerpt: string;
    reference_section: string | null;
  };
};

export type ResolveFindingResponse = {
  finding_id: number;
  finding_status: string;
  resolution_note: string;
};

export function getFindingDetail(id: string) {
  return apiGet<FindingDetailResponse>(`/findings/${id}`);
}

export function resolveFinding(findingId: string, resolutionNote: string) {
  return apiPost<ResolveFindingResponse, { resolution_note: string }>(
    `/findings/${findingId}/resolve`,
    { resolution_note: resolutionNote },
  );
}