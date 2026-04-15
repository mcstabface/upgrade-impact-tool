from pydantic import BaseModel


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    progress_pct: int
    current_stage: str


class AnalysisApplicationSummary(BaseModel):
    analysis_application_id: int
    application_name: str
    current_version: str
    target_version: str
    status: str
    findings_count: int


class AnalysisSummaryCounts(BaseModel):
    applies_count: int
    review_required_count: int
    unknown_count: int
    blocked_count: int


class AnalysisStalenessResponse(BaseModel):
    analysis_id: str
    status: str
    is_stale: bool
    triggers: list[str]
    stale_detected_utc: int | None
    recorded_snapshot_hash: str | None
    current_snapshot_hash: str | None
    recorded_kb_catalog_hash: str | None
    current_kb_catalog_hash: str
    recorded_analysis_input_hash: str | None
    current_analysis_input_hash: str


class AnalysisOverviewResponse(BaseModel):
    analysis_id: str
    customer_name: str
    environment_name: str
    analysis_date: int | None
    overall_status: str
    started_utc: int | None = None
    completed_utc: int | None = None
    duration_ms: int | None = None
    stale_reason: str | None = None
    stale_detected_utc: int | None = None
    previous_analysis_id: str | None = None
    summary: AnalysisSummaryCounts
    assumptions: list[str]
    missing_inputs: list[str]
    derived_risks: list[str]
    top_risks: list[str] = []
    top_actions: list[str] = []
    applications: list["AnalysisApplicationSummary"]


class AnalysisApplicationFindingItem(BaseModel):
    finding_id: int
    status: str
    severity: str
    change_taxonomy: str
    headline: str
    recommended_action: str | None
    kb_reference: str


class AnalysisApplicationDetailResponse(BaseModel):
    analysis_application_id: int
    application_name: str
    current_version: str
    target_version: str
    application_status: str
    findings: list[AnalysisApplicationFindingItem]