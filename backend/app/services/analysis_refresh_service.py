import hashlib
import time
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import AnalysisStatus
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisRefreshResponse
from app.services.analysis_execution_service import AnalysisExecutionService
from app.services.analysis_transition_service import AnalysisTransitionService


class AnalysisRefreshService:
    def __init__(self) -> None:
        self.repository = AnalysisRepository()
        self.transition_service = AnalysisTransitionService()
        self.execution_service = AnalysisExecutionService()

    def refresh_analysis(self, db: Session, previous_analysis_id: str) -> AnalysisRefreshResponse | None:
        context = self.repository.get_staleness_context(db, previous_analysis_id)
        if not context:
            return None

        if context["overall_status"] != AnalysisStatus.STALE.value:
            raise ValueError("Analysis must be STALE before refresh can start")

        active_snapshot = self.repository.get_active_snapshot_for_customer_environment(
            db,
            customer_id=context["customer_id"],
            environment_id=context["environment_id"],
        )
        if not active_snapshot:
            raise ValueError("No active snapshot found for analysis customer/environment")

        snapshot_hash = active_snapshot["content_hash"]
        kb_catalog_hash = self.repository.get_current_kb_catalog_hash(db)
        analysis_input_hash = hashlib.md5(
            f"{snapshot_hash}|{kb_catalog_hash}".encode("utf-8")
        ).hexdigest()

        new_analysis_id = f"anl_{uuid4().hex[:12]}"
        started_utc = int(time.time())

        self.repository.create_refresh_analysis_run(
            db=db,
            analysis_id=new_analysis_id,
            previous_analysis_id=previous_analysis_id,
            customer_id=context["customer_id"],
            environment_id=context["environment_id"],
            snapshot_id=active_snapshot["snapshot_id"],
            kb_catalog_hash=kb_catalog_hash,
            snapshot_hash=snapshot_hash,
            analysis_input_hash=analysis_input_hash,
            started_utc=started_utc,
        )

        self.repository.insert_state_transition(
            db,
            analysis_id=new_analysis_id,
            previous_state=None,
            new_state=AnalysisStatus.REQUIRES_REFRESH.value,
            trigger_event="REFRESH_ANALYSIS_CREATED",
            user_id="system",
            transition_utc=started_utc,
        )

        self.transition_service.transition_analysis(
            db=db,
            analysis_id=new_analysis_id,
            new_state=AnalysisStatus.ANALYSIS_RUNNING,
            trigger_event="START_REFRESH_ANALYSIS",
            user_id="system",
        )

        self.execution_service.execute(db, new_analysis_id)

        return AnalysisRefreshResponse(
            previous_analysis_id=previous_analysis_id,
            new_analysis_id=new_analysis_id,
            status=AnalysisStatus.ANALYSIS_RUNNING.value,
            started_utc=started_utc,
            snapshot_id=active_snapshot["snapshot_id"],
            snapshot_hash=snapshot_hash,
            kb_catalog_hash=kb_catalog_hash,
            analysis_input_hash=analysis_input_hash,
        )