import time
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.analysis_execution_service import AnalysisExecutionService
from app.core.enums import AnalysisStatus
from app.repositories.intake_repository import IntakeRepository
from app.schemas.intake_api import (
    IntakeCreateRequest,
    IntakeCreateResponse,
    IntakeDetailResponse,
    IntakeUpdateRequest,
    IntakeUpdateResponse,
    IntakeValidateResponse,
    StartAnalysisResponse,
)
from app.services.analysis_transition_service import AnalysisTransitionService
from app.services.intake_validation_service import IntakeValidationService
from app.services.snapshot_service import SnapshotService


class IntakeWorkflowService:
    def __init__(self) -> None:
        self.repository = IntakeRepository()
        self.transition_service = AnalysisTransitionService()
        self.validation_service = IntakeValidationService()
        self.snapshot_service = SnapshotService()
        self.execution_service = AnalysisExecutionService()

    def create_intake(self, db: Session, payload: IntakeCreateRequest) -> IntakeCreateResponse:
        created_utc = int(time.time())
        intake_id = f"intk_{uuid4().hex[:12]}"
        payload_json = {
            "customer_name": payload.customer_name,
            "environment_name": payload.environment_name,
            "environment_type": payload.environment_type.value,
            "applications": [],
        }

        self.repository.create_draft(
            db=db,
            intake_id=intake_id,
            customer_name=payload.customer_name,
            environment_name=payload.environment_name,
            environment_type=payload.environment_type.value,
            status=AnalysisStatus.DRAFT.value,
            payload_json=payload_json,
            created_utc=created_utc,
        )

        return IntakeCreateResponse(
            intake_id=intake_id,
            status=AnalysisStatus.DRAFT.value,
            created_utc=created_utc,
        )

    def get_intake(self, db: Session, intake_id: str) -> IntakeDetailResponse | None:
        row = self.repository.get_draft(db, intake_id)
        if not row:
            return None

        payload = row["payload_json"] or {}
        return IntakeDetailResponse(
            intake_id=row["intake_id"],
            status=row["status"],
            customer_name=row["customer_name"],
            environment_name=row["environment_name"],
            environment_type=row["environment_type"],
            applications=payload.get("applications", []),
        )

    def update_intake(
        self,
        db: Session,
        intake_id: str,
        patch: IntakeUpdateRequest,
    ) -> IntakeUpdateResponse | None:
        row = self.repository.get_draft(db, intake_id)
        if not row:
            return None

        payload_json = row["payload_json"] or {}
        patch_data = patch.model_dump(exclude_none=True)
        payload_json.update(patch_data)

        completeness_score = self._calculate_completeness(payload_json)
        updated_utc = int(time.time())

        self.repository.update_draft(
            db=db,
            intake_id=intake_id,
            status=row["status"],
            payload_json=payload_json,
            completeness_score=completeness_score,
            updated_utc=updated_utc,
        )

        return IntakeUpdateResponse(
            intake_id=intake_id,
            status=row["status"],
            completeness_score=completeness_score,
        )

    def validate_intake(self, db: Session, intake_id: str) -> IntakeValidateResponse | None:
        row = self.repository.get_draft(db, intake_id)
        if not row:
            return None

        payload = row["payload_json"] or {}
        validation_result = self.validation_service.validate(payload)

        self.repository.update_draft(
            db=db,
            intake_id=intake_id,
            status=validation_result.status,
            payload_json=payload,
            completeness_score=validation_result.completeness_score,
            updated_utc=int(time.time()),
        )

        return IntakeValidateResponse(
            intake_id=intake_id,
            status=validation_result.status,
            completeness_score=validation_result.completeness_score,
            missing_required_fields=validation_result.missing_required_fields,
            warnings=[] if validation_result.status == AnalysisStatus.BLOCKED.value else validation_result.warnings,
        )

    def start_analysis(self, db: Session, intake_id: str) -> StartAnalysisResponse | None:
        row = self.repository.get_draft(db, intake_id)
        if not row:
            return None
        if row["status"] != AnalysisStatus.INTAKE_VALIDATED.value:
            return None

        snapshot_id, content_hash = self.snapshot_service.persist_snapshot_for_intake(
            db=db,
            intake_row=row,
        )

        snapshot_row = db.execute(
            text("""
                SELECT customer_id, environment_id
                FROM customer_state_snapshots
                WHERE snapshot_id = :snapshot_id
            """),
            {"snapshot_id": snapshot_id},
        ).first()

        analysis_id = f"anl_{uuid4().hex[:12]}"
        started_utc = int(time.time())

        self.repository.create_analysis_run(
            db=db,
            analysis_id=analysis_id,
            customer_id=snapshot_row.customer_id,
            environment_id=snapshot_row.environment_id,
            snapshot_id=snapshot_id,
            status=AnalysisStatus.INTAKE_VALIDATED.value,
            started_utc=started_utc,
        )

        self.transition_service.transition_analysis(
            db=db,
            analysis_id=analysis_id,
            new_state=AnalysisStatus.ANALYSIS_RUNNING,
            trigger_event="START_ANALYSIS",
            user_id="system",
        )

        execution_result = self.execution_service.execute(db, analysis_id)
        print(f"analysis execution result: {execution_result}")

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        print(f"snapshot created/selected: snapshot_id={snapshot_id}, content_hash={content_hash}")

        return StartAnalysisResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus.ANALYSIS_RUNNING,
            started_utc=started_utc,
        )

    def _calculate_completeness(self, payload: dict) -> int:
        checks = [
            bool(payload.get("customer_name")),
            bool(payload.get("environment_name")),
            bool(payload.get("environment_type")),
            bool(payload.get("applications")),
            bool(payload.get("primary_technical_contact")),
            bool(payload.get("primary_business_contact")),
            bool(payload.get("environment_count")),
            bool(payload.get("environment_classification")),
            bool(payload.get("vendor_kb_documents")),
        ]
        score = round((sum(1 for item in checks if item) / len(checks)) * 100)
        return int(score)