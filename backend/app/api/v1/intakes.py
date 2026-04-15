from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import UserRole, require_roles
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

router = APIRouter(tags=["intakes"])
service = IntakeWorkflowService()


@router.post("/intakes", response_model=IntakeCreateResponse)
def create_intake(
    payload: IntakeCreateRequest,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_roles(UserRole.ANALYST, UserRole.ADMIN)),
) -> IntakeCreateResponse:
    return service.create_intake(db, payload)


@router.get("/intakes/{intake_id}", response_model=IntakeDetailResponse)
def get_intake(intake_id: str, db: Session = Depends(get_db)) -> IntakeDetailResponse:
    result = service.get_intake(db, intake_id)
    if not result:
        raise HTTPException(status_code=404, detail="Intake not found")
    return result


@router.patch("/intakes/{intake_id}", response_model=IntakeUpdateResponse)
def update_intake(
    intake_id: str,
    payload: IntakeUpdateRequest,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_roles(UserRole.ANALYST, UserRole.ADMIN)),
) -> IntakeUpdateResponse:
    result = service.update_intake(db, intake_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Intake not found")
    return result


@router.post("/intakes/{intake_id}/validate", response_model=IntakeValidateResponse)
def validate_intake(
    intake_id: str,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_roles(UserRole.ANALYST, UserRole.ADMIN)),
) -> IntakeValidateResponse:
    result = service.validate_intake(db, intake_id)
    if not result:
        raise HTTPException(status_code=404, detail="Intake not found")
    return result


@router.post("/intakes/{intake_id}/analyses", response_model=StartAnalysisResponse)
def start_analysis(
    intake_id: str,
    _: StartAnalysisRequest,
    db: Session = Depends(get_db),
    __: UserRole = Depends(require_roles(UserRole.ANALYST, UserRole.ADMIN)),
) -> StartAnalysisResponse:
    result = service.start_analysis(db, intake_id)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Intake must exist and be INTAKE_VALIDATED before analysis can start",
        )
    return result