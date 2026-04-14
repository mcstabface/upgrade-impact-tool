from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewQueueRepository:
    def get_open_review_items(self, db: Session) -> list[dict]:
        query = text("""
            SELECT
                af.finding_id,
                af.analysis_id,
                cr.application_name,
                af.finding_status,
                af.severity,
                af.headline,
                af.reason_for_status
            FROM analysis_findings af
            JOIN change_records cr ON cr.change_id = af.change_id
            WHERE af.finding_status IN ('UNKNOWN', 'REQUIRES_REVIEW', 'BLOCKED')
            ORDER BY af.analysis_id DESC, af.finding_id DESC
        """)
        return [dict(row._mapping) for row in db.execute(query).all()]