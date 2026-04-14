from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewActionService:
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

        return {
            "finding_id": finding_id,
            "finding_status": "RESOLVED",
            "resolution_note": resolution_note,
        }