from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisApplicationDetailResponse,
    AnalysisOverviewResponse,
    AnalysisStatusResponse,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analyses"])
service = AnalysisService()


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