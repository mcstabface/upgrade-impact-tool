from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, UserRole, require_roles
from app.db.session import get_db
from app.schemas.intake_api import (
    IntakeCreateRequest,
    IntakeCreateResponse,
    IntakeDetailResponse,
    IntakeUpdateRequest,
    IntakeUpdateResponse,
    IntakeValidateResponse,
    StartAnalysisRequest,
    StartAnalysisResponse,
)
from app.services.intake_workflow_service import IntakeWorkflowService
from app.services.usage_event_service import UsageEventService

router = APIRouter(tags=["intakes"])
service = IntakeWorkflowService()
usage_event_service = UsageEventService()


@router.post("/intakes", response_model=IntakeCreateResponse)
def create_intake(
    payload: IntakeCreateRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ANALYST, UserRole.ADMIN)
    ),
) -> IntakeCreateResponse:
    result = service.create_intake(db, payload)

    usage_event_service.record_event(
        db=db,
        event_type="INTAKE_CREATED",
        actor_role=current_user.role.value,
        actor_user_id=current_user.user_id,
        entity_type="INTAKE",
        entity_id=result.intake_id,
        event_payload={
            "environment_type": payload.environment_type.value,
            "customer_name": payload.customer_name,
            "environment_name": payload.environment_name,
        },
    )

    return result


@router.get("/intakes/{intake_id}", response_model=IntakeDetailResponse)
def get_intake(
    intake_id: str,
    db: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(
        require_roles(
            UserRole.VIEWER,
            UserRole.ANALYST,
            UserRole.REVIEWER,
            UserRole.ADMIN,
        )
    ),
) -> IntakeDetailResponse:
    result = service.get_intake(db, intake_id)
    if not result:
        raise HTTPException(status_code=404, detail="Intake not found")
    return result


@router.patch("/intakes/{intake_id}", response_model=IntakeUpdateResponse)
def update_intake(
    intake_id: str,
    payload: IntakeUpdateRequest,
    db: Session = Depends(get_db),
    _: AuthenticatedUser = Depends(
        require_roles(UserRole.ANALYST, UserRole.ADMIN)
    ),
) -> IntakeUpdateResponse:
    result = service.update_intake(db, intake_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Intake not found")
    return result


@router.post("/intakes/{intake_id}/validate", response_model=IntakeValidateResponse)
def validate_intake(
    intake_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ANALYST, UserRole.ADMIN)
    ),
) -> IntakeValidateResponse:
    result = service.validate_intake(db, intake_id)
    if not result:
        raise HTTPException(status_code=404, detail="Intake not found")

    event_type = "INTAKE_VALIDATED" if result.status == "INTAKE_VALIDATED" else "INTAKE_BLOCKED"

    usage_event_service.record_event(
        db=db,
        event_type=event_type,
        actor_role=current_user.role.value,
        actor_user_id=current_user.user_id,
        entity_type="INTAKE",
        entity_id=result.intake_id,
        event_payload={
            "status": result.status,
            "completeness_score": result.completeness_score,
            "missing_required_fields": result.missing_required_fields,
            "warnings": result.warnings,
        },
    )

    return result


@router.post("/intakes/{intake_id}/analyses", response_model=StartAnalysisResponse)
def start_analysis(
    intake_id: str,
    _: StartAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(
        require_roles(UserRole.ANALYST, UserRole.ADMIN)
    ),
) -> StartAnalysisResponse:
    result = service.start_analysis(db, intake_id)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Intake must exist and be INTAKE_VALIDATED before analysis can start",
        )

    usage_event_service.record_event(
        db=db,
        event_type="ANALYSIS_STARTED",
        actor_role=current_user.role.value,
        actor_user_id=current_user.user_id,
        entity_type="ANALYSIS",
        entity_id=result.analysis_id,
        related_analysis_id=result.analysis_id,
        event_payload={
            "intake_id": intake_id,
            "status": result.status,
            "started_utc": result.started_utc,
        },
        commit=False,
    )

    if result.status != "ANALYSIS_RUNNING":
        usage_event_service.record_event(
            db=db,
            event_type="ANALYSIS_COMPLETED",
            actor_role=current_user.role.value,
            actor_user_id=current_user.user_id,
            entity_type="ANALYSIS",
            entity_id=result.analysis_id,
            related_analysis_id=result.analysis_id,
            event_payload={
                "intake_id": intake_id,
                "status": result.status,
                "started_utc": result.started_utc,
            },
            commit=True,
        )
    else:
        db.commit()

    return result