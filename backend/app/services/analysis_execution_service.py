from sqlalchemy.orm import Session

from app.services.analysis_results_service import AnalysisResultsService
from app.services.findings_service import FindingsService


class AnalysisExecutionService:
    def __init__(self) -> None:
        self.findings_service = FindingsService()
        self.results_service = AnalysisResultsService()

    def execute(self, db: Session, analysis_id: str) -> dict:
        findings_result = self.findings_service.generate_findings_for_analysis(db, analysis_id)
        results_result = self.results_service.finalize_analysis(db, analysis_id)

        return {
            "analysis_id": analysis_id,
            "findings_created": findings_result["findings_created"],
            "final_status": results_result["final_status"],
            "applies_count": results_result["applies_count"],
            "review_required_count": results_result["review_required_count"],
            "unknown_count": results_result["unknown_count"],
            "blocked_count": results_result["blocked_count"],
        }