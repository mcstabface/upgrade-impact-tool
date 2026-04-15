from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.schemas.analysis import (
    AnalysisApplicationDetailResponse,
    AnalysisAuditResponse,
    AnalysisDeltaSummaryResponse,
    AnalysisOverviewResponse,
    AnalysisRefreshResponse,
    AnalysisStalenessResponse,
    AnalysisStatusResponse,
)
from app.services.analysis_application_export_service import AnalysisApplicationExportService
from app.services.analysis_audit_service import AnalysisAuditService
from app.services.analysis_delta_service import AnalysisDeltaService
from app.services.analysis_export_service import AnalysisExportService
from app.services.analysis_refresh_service import AnalysisRefreshService
from app.services.analysis_service import AnalysisService
from app.services.analysis_staleness_service import AnalysisStalenessService

from app.core.enums import AnalysisStatus
from app.services.analysis_transition_service import (
    AnalysisTransitionService,
    InvalidAnalysisTransitionError,
)

router = APIRouter(tags=["analyses"])
service = AnalysisService()
staleness_service = AnalysisStalenessService()
refresh_service = AnalysisRefreshService()
delta_service = AnalysisDeltaService()
audit_service = AnalysisAuditService()
export_service = AnalysisExportService()
application_export_service = AnalysisApplicationExportService()

transition_service = AnalysisTransitionService()


class AnalysisTransitionRequest(BaseModel):
    new_state: AnalysisStatus
    trigger_event: str


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


@router.post("/analyses/{analysis_id}/evaluate-staleness", response_model=AnalysisStalenessResponse)
def evaluate_analysis_staleness(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisStalenessResponse:
    try:
        result = staleness_service.evaluate_analysis(db, analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Staleness evaluation failed: {exc}",
        ) from exc


@router.post("/analyses/{analysis_id}/refresh", response_model=AnalysisRefreshResponse)
def refresh_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisRefreshResponse:
    try:
        result = refresh_service.refresh_analysis(db, analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Refresh analysis failed: {exc}",
        ) from exc


@router.get("/analyses/{analysis_id}/delta-summary", response_model=AnalysisDeltaSummaryResponse)
def get_analysis_delta_summary(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisDeltaSummaryResponse:
    result = delta_service.get_delta_summary(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Delta summary not available for analysis")
    return result


@router.get("/analyses/{analysis_id}/audit", response_model=AnalysisAuditResponse)
def get_analysis_audit(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> AnalysisAuditResponse:
    result = audit_service.get_audit(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/analyses/{analysis_id}/export.json")
def export_analysis_json(
    analysis_id: str,
    db: Session = Depends(get_db),
) -> Response:
    result = export_service.get_export(db, analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return Response(
        content=result.model_dump_json(indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{analysis_id}_export.json"',
        },
    )


@router.get("/analyses/{analysis_id}/applications/{analysis_application_id}/export.json")
def export_analysis_application_json(
    analysis_id: str,
    analysis_application_id: int,
    db: Session = Depends(get_db),
) -> Response:
    result = application_export_service.get_export(db, analysis_id, analysis_application_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis application not found")

    return Response(
        content=result.model_dump_json(indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{analysis_id}_application_{analysis_application_id}_export.json"'
            ),
        },
    )


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