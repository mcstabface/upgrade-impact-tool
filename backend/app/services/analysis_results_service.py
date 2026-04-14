import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.enums import AnalysisStatus
from app.services.analysis_transition_service import AnalysisTransitionService


class AnalysisResultsService:
    def __init__(self) -> None:
        self.transition_service = AnalysisTransitionService()

    def finalize_analysis(self, db: Session, analysis_id: str) -> dict:
        counts = db.execute(
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

        applies_count = counts.applies_count or 0
        review_required_count = counts.review_required_count or 0
        unknown_count = counts.unknown_count or 0
        blocked_count = counts.blocked_count or 0

        timing = db.execute(
            text("""
                SELECT started_utc
                FROM analysis_runs
                WHERE analysis_id = :analysis_id
            """),
            {"analysis_id": analysis_id},
        ).first()

        completed_utc = int(time.time())
        started_utc = timing.started_utc if timing and timing.started_utc else completed_utc
        duration_ms = max(0, (completed_utc - started_utc) * 1000)

        db.execute(
            text("""
                UPDATE analysis_runs
                SET
                    applies_count = :applies_count,
                    review_required_count = :review_required_count,
                    unknown_count = :unknown_count,
                    blocked_count = :blocked_count,
                    completed_utc = :completed_utc,
                    duration_ms = :duration_ms
                WHERE analysis_id = :analysis_id
            """),
            {
                "analysis_id": analysis_id,
                "applies_count": applies_count,
                "review_required_count": review_required_count,
                "unknown_count": unknown_count,
                "blocked_count": blocked_count,
                "completed_utc": completed_utc,
                "duration_ms": duration_ms,
            },
        )

        self.transition_service.transition_analysis(
            db=db,
            analysis_id=analysis_id,
            new_state=AnalysisStatus.ANALYSIS_COMPLETE,
            trigger_event="ANALYSIS_FINISHED",
            user_id="system",
        )

        final_state = (
            AnalysisStatus.REVIEW_REQUIRED
            if review_required_count > 0 or unknown_count > 0 or blocked_count > 0
            else AnalysisStatus.READY
        )

        self.transition_service.transition_analysis(
            db=db,
            analysis_id=analysis_id,
            new_state=final_state,
            trigger_event="FINDINGS_EVALUATED",
            user_id="system",
        )

        return {
            "analysis_id": analysis_id,
            "applies_count": applies_count,
            "review_required_count": review_required_count,
            "unknown_count": unknown_count,
            "blocked_count": blocked_count,
            "completed_utc": completed_utc,
            "duration_ms": duration_ms,
            "final_status": final_state.value,
        }