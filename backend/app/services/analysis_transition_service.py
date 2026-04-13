import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.enums import AnalysisStatus
from app.workflows.analysis_state_machine import can_transition


class InvalidAnalysisTransitionError(Exception):
    pass


class AnalysisTransitionService:
    def transition_analysis(
        self,
        db: Session,
        analysis_id: str,
        new_state: AnalysisStatus,
        trigger_event: str,
        user_id: str = "system",
    ) -> None:
        row = db.execute(
            text("""
                SELECT analysis_status
                FROM analysis_runs
                WHERE analysis_id = :analysis_id
            """),
            {"analysis_id": analysis_id},
        ).first()

        if not row:
            raise InvalidAnalysisTransitionError("Analysis not found")

        previous_state = AnalysisStatus(row.analysis_status)

        if not can_transition(previous_state, new_state):
            raise InvalidAnalysisTransitionError(
                f"Invalid transition: {previous_state.value} -> {new_state.value}"
            )

        transition_utc = int(time.time())

        db.execute(
            text("""
                UPDATE analysis_runs
                SET
                    analysis_status = :new_state,
                    overall_status = :new_state
                WHERE analysis_id = :analysis_id
            """),
            {
                "analysis_id": analysis_id,
                "new_state": new_state.value,
            },
        )

        db.execute(
            text("""
                INSERT INTO state_transitions (
                    analysis_id,
                    previous_state,
                    new_state,
                    trigger_event,
                    user_id,
                    transition_utc
                ) VALUES (
                    :analysis_id,
                    :previous_state,
                    :new_state,
                    :trigger_event,
                    :user_id,
                    :transition_utc
                )
            """),
            {
                "analysis_id": analysis_id,
                "previous_state": previous_state.value,
                "new_state": new_state.value,
                "trigger_event": trigger_event,
                "user_id": user_id,
                "transition_utc": transition_utc,
            },
        )