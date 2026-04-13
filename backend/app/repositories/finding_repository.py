from sqlalchemy import text
from sqlalchemy.orm import Session


class FindingRepository:
    def get_finding_detail(self, db: Session, finding_id: int) -> dict | None:
        query = text("""
            SELECT
                af.finding_id,
                af.finding_status AS status,
                af.severity,
                af.change_taxonomy,
                cr.application_name,
                cr.module_name,
                cr.version_from,
                cr.version_to,
                af.headline,
                af.plain_language_summary,
                af.business_impact_summary,
                af.technical_impact_summary,
                af.recommended_action,
                af.assumptions_text,
                af.missing_inputs_text,
                af.reason_for_status,
                fe.kb_article_number,
                fe.kb_title,
                fe.kb_url,
                fe.publication_date,
                fe.evidence_excerpt,
                fe.reference_section
            FROM analysis_findings af
            JOIN change_records cr ON cr.change_id = af.change_id
            JOIN finding_evidence fe ON fe.finding_id = af.finding_id
            WHERE af.finding_id = :finding_id
        """)
        row = db.execute(query, {"finding_id": finding_id}).first()
        return dict(row._mapping) if row else None