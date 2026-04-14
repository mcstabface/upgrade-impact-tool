from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.applicability_service import ApplicabilityService
from app.services.kb_provenance_service import KBProvenanceService, KBProvenanceValidationError


class FindingsService:
    def __init__(self) -> None:
        self.applicability_service = ApplicabilityService()
        self.provenance_service = KBProvenanceService()

    def generate_findings_for_analysis(self, db: Session, analysis_id: str) -> dict:
        analysis = db.execute(
            text("""
                SELECT analysis_id, snapshot_id
                FROM analysis_runs
                WHERE analysis_id = :analysis_id
            """),
            {"analysis_id": analysis_id},
        ).first()

        if not analysis:
            raise ValueError("Analysis not found")

        customer_apps = db.execute(
            text("""
                SELECT
                    customer_application_id,
                    application_name,
                    current_version,
                    target_version
                FROM customer_applications
                WHERE snapshot_id = :snapshot_id
                ORDER BY customer_application_id
            """),
            {"snapshot_id": analysis.snapshot_id},
        ).all()

        created = 0

        for app in customer_apps:
            analysis_app = db.execute(
                text("""
                    INSERT INTO analysis_applications (
                        analysis_id,
                        application_name,
                        current_version,
                        target_version,
                        application_status,
                        findings_count,
                        review_required_count,
                        blocked_count,
                        unknown_count
                    ) VALUES (
                        :analysis_id,
                        :application_name,
                        :current_version,
                        :target_version,
                        'ANALYSIS_RUNNING',
                        0, 0, 0, 0
                    )
                    RETURNING analysis_application_id
                """),
                {
                    "analysis_id": analysis.analysis_id,
                    "application_name": app.application_name,
                    "current_version": app.current_version,
                    "target_version": app.target_version,
                },
            ).first()

            modules = db.execute(
                text("""
                    SELECT module_name
                    FROM customer_modules
                    WHERE customer_application_id = :customer_application_id
                """),
                {"customer_application_id": app.customer_application_id},
            ).all()
            module_names = [row.module_name for row in modules]

            change_records = db.execute(
                text("""
                    SELECT
                        cr.change_id,
                        cr.application_name,
                        cr.module_name,
                        cr.version_from,
                        cr.version_to,
                        cr.change_taxonomy,
                        cr.severity,
                        cr.impact_type,
                        cr.headline,
                        cr.plain_language_summary,
                        cr.business_impact_summary,
                        cr.technical_impact_summary,
                        cr.recommended_action,
                        cr.customization_review_required,
                        cr.integration_review_required,
                        ka.kb_article_number,
                        ka.kb_title,
                        ka.kb_url,
                        ka.published_date
                    FROM change_records cr
                    JOIN kb_articles ka ON ka.kb_article_id = cr.kb_article_id
                    WHERE cr.application_name = :application_name
                    ORDER BY cr.change_id
                """),
                {"application_name": app.application_name},
            ).all()

            findings_count = 0
            review_required_count = 0
            blocked_count = 0
            unknown_count = 0

            for change in change_records:
                change_dict = dict(change._mapping)

                try:
                    self.provenance_service.validate_change_record_provenance(change_dict)
                    kb_provenance_present = True
                except KBProvenanceValidationError:
                    kb_provenance_present = False

                status, reason = self.applicability_service.evaluate(
                    customer_application={
                        "application_name": app.application_name,
                        "current_version": app.current_version,
                        "target_version": app.target_version,
                    },
                    customer_modules=module_names,
                    change_record=change_dict,
                    has_customizations=None,
                    has_integrations=None,
                    kb_provenance_present=kb_provenance_present,
                )

                if status == "DOES_NOT_APPLY":
                    continue

                finding = db.execute(
                    text("""
                        INSERT INTO analysis_findings (
                            analysis_id,
                            analysis_application_id,
                            change_id,
                            finding_status,
                            severity,
                            change_taxonomy,
                            impact_type,
                            headline,
                            plain_language_summary,
                            business_impact_summary,
                            technical_impact_summary,
                            recommended_action,
                            reason_for_status,
                            assumptions_text,
                            missing_inputs_text,
                            requires_review,
                            is_blocking,
                            created_utc
                        ) VALUES (
                            :analysis_id,
                            :analysis_application_id,
                            :change_id,
                            :finding_status,
                            :severity,
                            :change_taxonomy,
                            :impact_type,
                            :headline,
                            :plain_language_summary,
                            :business_impact_summary,
                            :technical_impact_summary,
                            :recommended_action,
                            :reason_for_status,
                            :assumptions_text,
                            :missing_inputs_text,
                            :requires_review,
                            :is_blocking,
                            EXTRACT(EPOCH FROM NOW())::bigint
                        )
                        RETURNING finding_id
                    """),
                    {
                        "analysis_id": analysis.analysis_id,
                        "analysis_application_id": analysis_app.analysis_application_id,
                        "change_id": change.change_id,
                        "finding_status": status,
                        "severity": change.severity,
                        "change_taxonomy": change.change_taxonomy,
                        "impact_type": change.impact_type,
                        "headline": change.headline,
                        "plain_language_summary": change.plain_language_summary,
                        "business_impact_summary": change.business_impact_summary,
                        "technical_impact_summary": change.technical_impact_summary,
                        "recommended_action": change.recommended_action,
                        "reason_for_status": reason,
                        "assumptions_text": "Standard application usage assumed.",
                        "missing_inputs_text": "Customization/integration inventory not provided."
                        if status in {"UNKNOWN", "REQUIRES_REVIEW"}
                        else None,
                        "requires_review": status == "REQUIRES_REVIEW",
                        "is_blocking": status == "BLOCKED",
                    },
                ).first()

                db.execute(
                    text("""
                        INSERT INTO finding_evidence (
                            finding_id,
                            kb_article_number,
                            kb_title,
                            kb_url,
                            publication_date,
                            evidence_excerpt,
                            reference_section
                        ) VALUES (
                            :finding_id,
                            :kb_article_number,
                            :kb_title,
                            :kb_url,
                            :publication_date,
                            :evidence_excerpt,
                            'Seeded Evidence'
                        )
                    """),
                    {
                        "finding_id": finding.finding_id,
                        "kb_article_number": change.kb_article_number,
                        "kb_title": change.kb_title,
                        "kb_url": change.kb_url,
                        "publication_date": change.published_date,
                        "evidence_excerpt": change.plain_language_summary,
                    },
                )

                findings_count += 1
                created += 1
                if status == "REQUIRES_REVIEW":
                    review_required_count += 1
                if status == "BLOCKED":
                    blocked_count += 1
                if status == "UNKNOWN":
                    unknown_count += 1

            db.execute(
                text("""
                    UPDATE analysis_applications
                    SET
                        application_status = CASE
                            WHEN :review_required_count > 0 THEN 'REVIEW_REQUIRED'
                            WHEN :blocked_count > 0 THEN 'BLOCKED'
                            WHEN :unknown_count > 0 THEN 'UNKNOWN'
                            ELSE 'READY'
                        END,
                        findings_count = :findings_count,
                        review_required_count = :review_required_count,
                        blocked_count = :blocked_count,
                        unknown_count = :unknown_count
                    WHERE analysis_application_id = :analysis_application_id
                """),
                {
                    "analysis_application_id": analysis_app.analysis_application_id,
                    "findings_count": findings_count,
                    "review_required_count": review_required_count,
                    "blocked_count": blocked_count,
                    "unknown_count": unknown_count,
                },
            )

        return {"analysis_id": analysis_id, "findings_created": created}