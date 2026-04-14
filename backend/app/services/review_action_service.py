from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.analysis_recompute_service import AnalysisRecomputeService


class ReviewActionService:
    def __init__(self) -> None:
        self.recompute_service = AnalysisRecomputeService()

    def resolve_finding(
        self,
        db: Session,
        finding_id: int,
        resolution_note: str,
    ) -> dict | None:
        row = db.execute(
            text("""
                SELECT finding_id, analysis_id
                FROM analysis_findings
                WHERE finding_id = :finding_id
            """),
            {"finding_id": finding_id},
        ).first()

        if not row:
            return None

        db.execute(
            text("""
                UPDATE analysis_findings
                SET
                    finding_status = 'RESOLVED',
                    reason_for_status = :resolution_note,
                    requires_review = false,
                    is_blocking = false
                WHERE finding_id = :finding_id
            """),
            {
                "finding_id": finding_id,
                "resolution_note": resolution_note,
            },
        )

        recompute_result = self.recompute_service.recompute_for_analysis(
            db=db,
            analysis_id=row.analysis_id,
        )

        return {
            "finding_id": finding_id,
            "finding_status": "RESOLVED",
            "resolution_note": resolution_note,
            "analysis_status": recompute_result["overall_status"],
        }