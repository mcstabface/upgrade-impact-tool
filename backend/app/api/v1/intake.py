from uuid import uuid4

from fastapi import APIRouter

from app.core.enums import AnalysisStatus
from app.schemas.intake import IntakeCreateResponse, IntakeRequest

router = APIRouter(tags=["intake"])


@router.post("/intake", response_model=IntakeCreateResponse)
def create_intake(payload: IntakeRequest) -> IntakeCreateResponse:
    warnings: list[str] = []

    if not payload.integrations:
        warnings.append("No integration inventory provided.")
    if not payload.customizations:
        warnings.append("No customization inventory provided.")
    if not payload.jobs:
        warnings.append("Job inventory is incomplete or not provided.")

    return IntakeCreateResponse(
        analysis_id=f"analysis_{uuid4().hex[:12]}",
        analysis_status=AnalysisStatus.INTAKE_VALIDATED,
        warnings=warnings,
        applications_in_scope=len(payload.applications),
        environment_count=payload.environment_count,
    )