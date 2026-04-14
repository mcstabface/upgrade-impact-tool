from sqlalchemy import text
from sqlalchemy.orm import Session


class AnalysisRecomputeService:
    def recompute_for_analysis(self, db: Session, analysis_id: str) -> dict:
        application_rows = db.execute(
            text("""
                SELECT analysis_application_id
                FROM analysis_applications
                WHERE analysis_id = :analysis_id
                ORDER BY analysis_application_id
            """),
            {"analysis_id": analysis_id},
        ).all()

        for row in application_rows:
            counts = db.execute(
                text("""
                    SELECT
                        COUNT(*) FILTER (WHERE finding_status = 'APPLIES') AS applies_count,
                        COUNT(*) FILTER (WHERE finding_status = 'REQUIRES_REVIEW') AS review_required_count,
                        COUNT(*) FILTER (WHERE finding_status = 'UNKNOWN') AS unknown_count,
                        COUNT(*) FILTER (WHERE finding_status = 'BLOCKED') AS blocked_count,
                        COUNT(*) FILTER (WHERE finding_status = 'RESOLVED') AS resolved_count,
                        COUNT(*) AS findings_count
                    FROM analysis_findings
                    WHERE analysis_application_id = :analysis_application_id
                """),
                {"analysis_application_id": row.analysis_application_id},
            ).first()

            review_required_count = counts.review_required_count or 0
            unknown_count = counts.unknown_count or 0
            blocked_count = counts.blocked_count or 0
            findings_count = counts.findings_count or 0

            if blocked_count > 0:
                application_status = "BLOCKED"
            elif review_required_count > 0:
                application_status = "REVIEW_REQUIRED"
            elif unknown_count > 0:
                application_status = "UNKNOWN"
            elif findings_count > 0:
                application_status = "READY"
            else:
                application_status = "READY"

            db.execute(
                text("""
                    UPDATE analysis_applications
                    SET
                        application_status = :application_status,
                        findings_count = :findings_count,
                        review_required_count = :review_required_count,
                        blocked_count = :blocked_count,
                        unknown_count = :unknown_count
                    WHERE analysis_application_id = :analysis_application_id
                """),
                {
                    "analysis_application_id": row.analysis_application_id,
                    "application_status": application_status,
                    "findings_count": findings_count,
                    "review_required_count": review_required_count,
                    "blocked_count": blocked_count,
                    "unknown_count": unknown_count,
                },
            )

        analysis_counts = db.execute(
            text("""
                SELECT
                    COUNT(*) FILTER (WHERE finding_status = 'APPLIES') AS applies_count,
                    COUNT(*) FILTER (WHERE finding_status = 'REQUIRES_REVIEW') AS review_required_count,
                    COUNT(*) FILTER (WHERE finding_status = 'UNKNOWN') AS unknown_count,
                    COUNT(*) FILTER (WHERE finding_status = 'BLOCKED') AS blocked_count
                FROM analysis_findings
                WHERE analysis_id = :analysis_id
            """),
            {"analysis_id": analysis_id},
        ).first()

        applies_count = analysis_counts.applies_count or 0
        review_required_count = analysis_counts.review_required_count or 0
        unknown_count = analysis_counts.unknown_count or 0
        blocked_count = analysis_counts.blocked_count or 0

        if blocked_count > 0:
            overall_status = "BLOCKED"
        elif review_required_count > 0 or unknown_count > 0:
            overall_status = "REVIEW_REQUIRED"
        else:
            overall_status = "READY"

        db.execute(
            text("""
                UPDATE analysis_runs
                SET
                    applies_count = :applies_count,
                    review_required_count = :review_required_count,
                    unknown_count = :unknown_count,
                    blocked_count = :blocked_count,
                    analysis_status = :overall_status,
                    overall_status = :overall_status
                WHERE analysis_id = :analysis_id
            """),
            {
                "analysis_id": analysis_id,
                "applies_count": applies_count,
                "review_required_count": review_required_count,
                "unknown_count": unknown_count,
                "blocked_count": blocked_count,
                "overall_status": overall_status,
            },
        )

        return {
            "analysis_id": analysis_id,
            "applies_count": applies_count,
            "review_required_count": review_required_count,
            "unknown_count": unknown_count,
            "blocked_count": blocked_count,
            "overall_status": overall_status,
        }