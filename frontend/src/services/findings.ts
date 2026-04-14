import { apiGet } from "./api";

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

export function getFindingDetail(id: string) {
  return apiGet<FindingDetailResponse>(`/findings/${id}`);
}

export async function resolveFinding(findingId: string, resolutionNote: string) {
  const response = await fetch(`http://localhost:8000/api/v1/findings/${findingId}/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ resolution_note: resolutionNote }),
  });

  if (!response.ok) {
    throw new Error(`POST /findings/${findingId}/resolve failed with status ${response.status}`);
  }

  return response.json();
}