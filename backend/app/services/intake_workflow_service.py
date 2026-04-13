import time
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.analysis_transition_service import AnalysisTransitionService
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


class IntakeWorkflowService:
    def __init__(self) -> None:
        self.repository = IntakeRepository()
        self.transition_service = AnalysisTransitionService()

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
        missing_required_fields = []

        applications = payload.get("applications") or []
        if not applications:
            missing_required_fields.append("applications")

        if not payload.get("vendor_kb_documents"):
            missing_required_fields.append("vendor_kb_documents")

        for app in applications:
            if not app.get("current_version"):
                missing_required_fields.append("current_version")
            if not app.get("target_version"):
                missing_required_fields.append("target_version")
            if not app.get("modules_enabled"):
                missing_required_fields.append("modules_enabled")

        missing_required_fields = sorted(set(missing_required_fields))
        warnings = []

        if not payload.get("integrations"):
            warnings.append("No integration inventory provided")
        if not payload.get("customizations"):
            warnings.append("No customization inventory provided")
        if not payload.get("jobs"):
            warnings.append("Job inventory is incomplete or not provided")

        completeness_score = self._calculate_completeness(payload)

        if missing_required_fields:
            new_status = AnalysisStatus.BLOCKED.value
            self.repository.update_draft(
                db=db,
                intake_id=intake_id,
                status=new_status,
                payload_json=payload,
                completeness_score=completeness_score,
                updated_utc=int(time.time()),
            )
            return IntakeValidateResponse(
                intake_id=intake_id,
                status=new_status,
                missing_required_fields=missing_required_fields,
                warnings=[],
            )

        new_status = AnalysisStatus.INTAKE_VALIDATED.value
        self.repository.update_draft(
            db=db,
            intake_id=intake_id,
            status=new_status,
            payload_json=payload,
            completeness_score=completeness_score,
            updated_utc=int(time.time()),
        )
        return IntakeValidateResponse(
            intake_id=intake_id,
            status=new_status,
            completeness_score=completeness_score,
            missing_required_fields=[],
            warnings=warnings,
        )

    def start_analysis(self, db: Session, intake_id: str) -> StartAnalysisResponse | None:
        row = self.repository.get_draft(db, intake_id)
        if not row:
            return None
        if row["status"] != AnalysisStatus.INTAKE_VALIDATED.value:
            return None

        analysis_id = f"anl_{uuid4().hex[:12]}"
        started_utc = int(time.time())

        self.repository.create_analysis_run(
            db=db,
            analysis_id=analysis_id,
            customer_id=1,
            environment_id=1,
            snapshot_id=1,
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

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

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