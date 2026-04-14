from pydantic import BaseModel


class DashboardAnalysisItem(BaseModel):
    analysis_id: str
    customer_name: str
    environment_name: str
    analysis_date: int | None
    overall_status: str
    applications_count: int
    applies_count: int
    review_required_count: int
    unknown_count: int
    blocked_count: int


class DashboardResponse(BaseModel):
    analyses: list[DashboardAnalysisItem]
    top_risks: list[str] = []
    top_actions: list[str] = []