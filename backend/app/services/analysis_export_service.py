import time

from sqlalchemy.orm import Session

from app.schemas.analysis import AnalysisExportResponse
from app.services.analysis_audit_service import AnalysisAuditService
from app.services.analysis_delta_service import AnalysisDeltaService
from app.services.analysis_service import AnalysisService


class AnalysisExportService:
    def __init__(self) -> None:
        self.analysis_service = AnalysisService()
        self.delta_service = AnalysisDeltaService()
        self.audit_service = AnalysisAuditService()

    def get_export(self, db: Session, analysis_id: str) -> AnalysisExportResponse | None:
        analysis = self.analysis_service.get_overview(db, analysis_id)
        if not analysis:
            return None

        delta_summary = self.delta_service.get_delta_summary(db, analysis_id)
        audit = self.audit_service.get_audit(db, analysis_id)
        if not audit:
            return None

        return AnalysisExportResponse(
            exported_at_utc=int(time.time()),
            analysis=analysis,
            delta_summary=delta_summary,
            audit=audit,
        )