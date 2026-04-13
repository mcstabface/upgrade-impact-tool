from pydantic import BaseModel


class VersionRange(BaseModel):
    from_version: str | None
    to_version: str | None


class FindingEvidenceResponse(BaseModel):
    kb_article_number: str
    kb_title: str
    kb_url: str
    publication_date: str
    evidence_excerpt: str
    reference_section: str | None


class FindingDetailResponse(BaseModel):
    finding_id: int
    status: str
    severity: str
    change_taxonomy: str
    application_name: str
    module_name: str | None
    version_range: VersionRange
    headline: str
    plain_language_summary: str
    business_impact_summary: str | None
    technical_impact_summary: str | None
    recommended_action: str | None
    assumptions: list[str]
    missing_inputs: list[str]
    reason_for_status: str | None
    evidence: FindingEvidenceResponse