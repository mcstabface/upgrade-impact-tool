from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisApplicationDetailResponse,
    AnalysisOverviewResponse,
    AnalysisStatusResponse,
)
from app.services.analysis_service import AnalysisService

from app.core.enums import AnalysisStatus
from app.services.analysis_transition_service import (
    AnalysisTransitionService,
    InvalidAnalysisTransitionError,
)

router = APIRouter(tags=["analyses"])
service = AnalysisService()

transition_service = AnalysisTransitionService()


class AnalysisTransitionRequest(BaseModel):
    new_state: AnalysisStatus
    trigger_event: str

    model_config = {"use_enum_values": True}


@router.post("/analyses/{analysis_id}/transition", response_model=AnalysisStatusResponse)
def transition_analysis(
    analysis_id: str,
    payload: AnalysisTransitionRequest,
    db: Session = Depends(get_db),
) -> AnalysisStatusResponse:
    try:
        transition_service.transition_analysis(
            db=db,
            analysis_id=analysis_id,
            new_state=payload.new_state,
            trigger_event=payload.trigger_event,
            user_id="system",
        )
        db.commit()
    except InvalidAnalysisTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    result = service.get_status(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result

@router.get("/analyses/{analysis_id}/status", response_model=AnalysisStatusResponse)
def get_analysis_status(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisStatusResponse:
    result = service.get_status(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/analyses/{analysis_id}", response_model=AnalysisOverviewResponse)
def get_analysis_overview(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisOverviewResponse:
    result = service.get_overview(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get(
    "/analyses/{analysis_id}/applications/{analysis_application_id}",
    response_model=AnalysisApplicationDetailResponse,
)
def get_analysis_application_detail(
    analysis_id: str,
    analysis_application_id: int,
    db: Session = Depends(get_db),
) -> AnalysisApplicationDetailResponse:
    result = service.get_application_detail(db, analysis_id, analysis_application_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis application not found")
    return result