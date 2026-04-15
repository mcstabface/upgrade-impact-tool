from sqlalchemy.orm import Session

from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import (
    AnalysisAuditResponse,
    AnalysisLineageNode,
    AnalysisStateTransitionItem,
)


class AnalysisAuditService:
    def __init__(self) -> None:
        self.repository = AnalysisRepository()

    def get_audit(self, db: Session, analysis_id: str) -> AnalysisAuditResponse | None:
        lineage_rows = self.repository.get_lineage_chain(db, analysis_id)
        if not lineage_rows:
            return None

        analysis_ids = [row["analysis_id"] for row in lineage_rows]
        transition_rows = self.repository.get_state_transitions_for_lineage(db, analysis_ids)

        return AnalysisAuditResponse(
            analysis_id=analysis_id,
            lineage=[AnalysisLineageNode(**row) for row in lineage_rows],
            transitions=[AnalysisStateTransitionItem(**row) for row in transition_rows],
        )