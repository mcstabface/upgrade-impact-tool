from sqlalchemy.orm import Session

from app.repositories.finding_repository import FindingRepository
from app.schemas.finding import (
    FindingDetailResponse,
    FindingEvidenceResponse,
    VersionRange,
)


class FindingService:
    def __init__(self) -> None:
        self.repository = FindingRepository()

    def get_finding_detail(self, db: Session, finding_id: int) -> FindingDetailResponse | None:
        row = self.repository.get_finding_detail(db, finding_id)
        if not row:
            return None

        assumptions = [row["assumptions_text"]] if row["assumptions_text"] else []
        missing_inputs = [row["missing_inputs_text"]] if row["missing_inputs_text"] else []

        return FindingDetailResponse(
            finding_id=row["finding_id"],
            status=row["status"],
            severity=row["severity"],
            change_taxonomy=row["change_taxonomy"],
            application_name=row["application_name"],
            module_name=row["module_name"],
            version_range=VersionRange(
                from_version=row["version_from"],
                to_version=row["version_to"],
            ),
            headline=row["headline"],
            plain_language_summary=row["plain_language_summary"],
            business_impact_summary=row["business_impact_summary"],
            technical_impact_summary=row["technical_impact_summary"],
            recommended_action=row["recommended_action"],
            assumptions=assumptions,
            missing_inputs=missing_inputs,
            reason_for_status=row["reason_for_status"],
            evidence=FindingEvidenceResponse(
                kb_article_number=row["kb_article_number"],
                kb_title=row["kb_title"],
                kb_url=row["kb_url"],
                publication_date=row["publication_date"],
                evidence_excerpt=row["evidence_excerpt"],
                reference_section=row["reference_section"],
            ),
        )