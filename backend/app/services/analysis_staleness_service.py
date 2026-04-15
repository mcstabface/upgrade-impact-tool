import hashlib
import time

from sqlalchemy.orm import Session

from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisStalenessResponse


class AnalysisStalenessService:
    def __init__(self) -> None:
        self.repository = AnalysisRepository()

    def evaluate_analysis(self, db: Session, analysis_id: str) -> AnalysisStalenessResponse | None:
        context = self.repository.get_staleness_context(db, analysis_id)
        if not context:
            return None

        current_snapshot_hash = self.repository.get_snapshot_hash(db, context["snapshot_id"])
        if current_snapshot_hash is None:
            raise ValueError("Snapshot hash not found for analysis snapshot")

        current_kb_catalog_hash = self.repository.get_current_kb_catalog_hash(db)
        current_analysis_input_hash = hashlib.md5(
            f"{current_snapshot_hash}|{current_kb_catalog_hash}".encode("utf-8")
        ).hexdigest()

        triggers: list[str] = []

        if context["recorded_kb_catalog_hash"] != current_kb_catalog_hash:
            triggers.append("KB_CATALOG_CHANGED")

        if context["recorded_snapshot_hash"] != current_snapshot_hash:
            triggers.append("SNAPSHOT_CHANGED")

        if context["recorded_analysis_input_hash"] != current_analysis_input_hash:
            triggers.append("ANALYSIS_INPUT_CHANGED")

        is_stale = len(triggers) > 0
        stale_detected_utc = context["stale_detected_utc"]

        if is_stale and context["overall_status"] != "STALE":
            stale_detected_utc = int(time.time())
            stale_reason = ", ".join(triggers)

            self.repository.mark_analysis_stale(
                db,
                analysis_id=analysis_id,
                stale_reason=stale_reason,
                stale_detected_utc=stale_detected_utc,
            )
            self.repository.insert_state_transition(
                db,
                analysis_id=analysis_id,
                previous_state=context["overall_status"],
                new_state="STALE",
                trigger_event="PHASE4_STALENESS_EVALUATION",
                user_id="system",
                transition_utc=stale_detected_utc,
            )

        return AnalysisStalenessResponse(
            analysis_id=context["analysis_id"],
            status="STALE" if is_stale else context["overall_status"],
            is_stale=is_stale,
            triggers=triggers,
            stale_detected_utc=stale_detected_utc,
            recorded_snapshot_hash=context["recorded_snapshot_hash"],
            current_snapshot_hash=current_snapshot_hash,
            recorded_kb_catalog_hash=context["recorded_kb_catalog_hash"],
            current_kb_catalog_hash=current_kb_catalog_hash,
            recorded_analysis_input_hash=context["recorded_analysis_input_hash"],
            current_analysis_input_hash=current_analysis_input_hash,
        )