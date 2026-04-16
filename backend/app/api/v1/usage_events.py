from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.auth import UserRole, require_roles
from app.db.session import get_db
from app.schemas.usage_events import ResultsOverviewSessionEventRequest
from app.services.usage_event_service import UsageEventService

router = APIRouter(tags=["usage-events"])
usage_event_service = UsageEventService()


@router.post("/usage-events/results-overview-session", status_code=204)
def record_results_overview_session(
    payload: ResultsOverviewSessionEventRequest,
    db: Session = Depends(get_db),
    role: UserRole = Depends(
        require_roles(
            UserRole.VIEWER,
            UserRole.ANALYST,
            UserRole.REVIEWER,
            UserRole.ADMIN,
        )
    ),
) -> Response:
    usage_event_service.record_event(
        db=db,
        event_type="RESULTS_OVERVIEW_SESSION_RECORDED",
        actor_role=role.value,
        actor_user_id="system",
        entity_type="ANALYSIS",
        entity_id=payload.analysis_id,
        related_analysis_id=payload.analysis_id,
        event_payload={
            "analysis_id": payload.analysis_id,
            "duration_seconds": payload.duration_seconds,
        },
    )

    return Response(status_code=204)