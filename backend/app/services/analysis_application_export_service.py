import time

from sqlalchemy.orm import Session

from app.schemas.analysis import AnalysisApplicationExportResponse
from app.services.analysis_service import AnalysisService


class AnalysisApplicationExportService:
    def __init__(self) -> None:
        self.analysis_service = AnalysisService()

    def get_export(
        self,
        db: Session,
        analysis_id: str,
        analysis_application_id: int,
    ) -> AnalysisApplicationExportResponse | None:
        application = self.analysis_service.get_application_detail(
            db,
            analysis_id,
            analysis_application_id,
        )
        if not application:
            return None

        return AnalysisApplicationExportResponse(
            exported_at_utc=int(time.time()),
            analysis_id=analysis_id,
            analysis_application_id=analysis_application_id,
            application=application,
        )