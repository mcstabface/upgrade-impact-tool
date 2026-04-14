from sqlalchemy.orm import Session

from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import (
    AnalysisApplicationDetailResponse,
    AnalysisApplicationFindingItem,
    AnalysisApplicationSummary,
    AnalysisOverviewResponse,
    AnalysisStatusResponse,
    AnalysisSummaryCounts,
)


class AnalysisService:
    def __init__(self) -> None:
        self.repository = AnalysisRepository()

    def get_status(self, db: Session, analysis_id: str) -> AnalysisStatusResponse | None:
        row = self.repository.get_status(db, analysis_id)
        if not row:
            return None

        status = row["analysis_status"]
        progress_pct = 100 if status in {"ANALYSIS_COMPLETE", "REVIEW_REQUIRED", "READY"} else 10
        current_stage = "COMPLETE" if progress_pct == 100 else "INITIALIZED"

        return AnalysisStatusResponse(
            analysis_id=row["analysis_id"],
            status=status,
            progress_pct=progress_pct,
            current_stage=current_stage,
        )

    def get_overview(self, db: Session, analysis_id: str) -> AnalysisOverviewResponse | None:
        header = self.repository.get_overview_header(db, analysis_id)
        if not header:
            return None

        applications = self.repository.get_overview_applications(db, analysis_id)

        supporting = self.repository.get_overview_supporting_lists(db, analysis_id)

        return AnalysisOverviewResponse(
            analysis_id=header["analysis_id"],
            customer_name=header["customer_name"],
            environment_name=header["environment_name"],
            analysis_date=header["analysis_date"],
            overall_status=header["overall_status"],
            summary=AnalysisSummaryCounts(
                applies_count=header["applies_count"],
                review_required_count=header["review_required_count"],
                unknown_count=header["unknown_count"],
                blocked_count=header["blocked_count"],
            ),
            assumptions=supporting["assumptions"],
            missing_inputs=supporting["missing_inputs"],
            derived_risks=supporting["derived_risks"],
            started_utc=header["started_utc"],
            completed_utc=header["completed_utc"],
            duration_ms=header["duration_ms"],
            applications=[AnalysisApplicationSummary(**row) for row in applications],
        )

    def get_application_detail(
        self, db: Session, analysis_id: str, analysis_application_id: int
    ) -> AnalysisApplicationDetailResponse | None:
        header = self.repository.get_application_detail(db, analysis_id, analysis_application_id)
        if not header:
            return None

        findings = self.repository.get_application_findings(db, analysis_application_id)
        return AnalysisApplicationDetailResponse(
            analysis_application_id=header["analysis_application_id"],
            application_name=header["application_name"],
            current_version=header["current_version"],
            target_version=header["target_version"],
            application_status=header["application_status"],
            findings=[
                AnalysisApplicationFindingItem(
                    finding_id=row["finding_id"],
                    status=row["status"],
                    severity=row["severity"],
                    change_taxonomy=row["change_taxonomy"],
                    headline=row["headline"],
                    recommended_action=row["recommended_action"],
                    kb_reference=row["kb_article_number"],
                )
                for row in findings
            ],
        )