from sqlalchemy import text
from sqlalchemy.orm import Session


class AnalysisRepository:
    def get_status(self, db: Session, analysis_id: str) -> dict | None:
        query = text("""
            SELECT analysis_id, analysis_status
            FROM analysis_runs
            WHERE analysis_id = :analysis_id
        """)
        row = db.execute(query, {"analysis_id": analysis_id}).first()
        return dict(row._mapping) if row else None

    def get_overview_header(self, db: Session, analysis_id: str) -> dict | None:
        query = text("""
            SELECT
                ar.analysis_id,
                c.customer_name,
                e.environment_name,
                ar.completed_utc AS analysis_date,
                ar.overall_status,
                ar.applies_count,
                ar.review_required_count,
                ar.unknown_count,
                ar.started_utc,
                ar.completed_utc,
                ar.duration_ms,
                ar.blocked_count                
            FROM analysis_runs ar
            JOIN customers c ON c.customer_id = ar.customer_id
            JOIN environments e ON e.environment_id = ar.environment_id
            WHERE ar.analysis_id = :analysis_id
        """)
        row = db.execute(query, {"analysis_id": analysis_id}).first()
        return dict(row._mapping) if row else None

    def get_overview_applications(self, db: Session, analysis_id: str) -> list[dict]:
        query = text("""
            SELECT
                analysis_application_id,
                application_name,
                current_version,
                target_version,
                application_status AS status,
                findings_count
            FROM analysis_applications
            WHERE analysis_id = :analysis_id
            ORDER BY analysis_application_id
        """)
        return [dict(row._mapping) for row in db.execute(query, {"analysis_id": analysis_id}).all()]

    def get_application_detail(self, db: Session, analysis_id: str, analysis_application_id: int) -> dict | None:
        query = text("""
            SELECT
                analysis_application_id,
                application_name,
                current_version,
                target_version,
                application_status
            FROM analysis_applications
            WHERE analysis_id = :analysis_id
              AND analysis_application_id = :analysis_application_id
        """)
        row = db.execute(
            query,
            {"analysis_id": analysis_id, "analysis_application_id": analysis_application_id},
        ).first()
        return dict(row._mapping) if row else None

    def get_application_findings(self, db: Session, analysis_application_id: int) -> list[dict]:
        query = text("""
            SELECT
                af.finding_id,
                af.finding_status AS status,
                af.severity,
                af.change_taxonomy,
                af.headline,
                af.recommended_action,
                fe.kb_article_number
            FROM analysis_findings af
            JOIN finding_evidence fe ON fe.finding_id = af.finding_id
            WHERE af.analysis_application_id = :analysis_application_id
            ORDER BY af.finding_id
        """)
        return [dict(row._mapping) for row in db.execute(query, {"analysis_application_id": analysis_application_id}).all()]

    def get_top_risks(self, db: Session, analysis_id: str) -> list[str]:
        rows = db.execute(
            text("""
                SELECT headline
                FROM analysis_findings
                WHERE analysis_id = :analysis_id
                  AND finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN')
                ORDER BY
                  CASE finding_status
                    WHEN 'BLOCKED' THEN 1
                    WHEN 'REQUIRES_REVIEW' THEN 2
                    WHEN 'UNKNOWN' THEN 3
                    ELSE 99
                  END,
                  CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    WHEN 'LOW' THEN 4
                    ELSE 99
                  END,
                  headline
                LIMIT 5
            """),
            {"analysis_id": analysis_id},
        ).all()

        return [row.headline for row in rows]

    def get_top_actions(self, db: Session, analysis_id: str) -> list[str]:
        rows = db.execute(
            text("""
                SELECT recommended_action
                FROM analysis_findings
                WHERE analysis_id = :analysis_id
                  AND recommended_action IS NOT NULL
                  AND recommended_action <> ''
                ORDER BY
                  CASE finding_status
                    WHEN 'BLOCKED' THEN 1
                    WHEN 'REQUIRES_REVIEW' THEN 2
                    WHEN 'UNKNOWN' THEN 3
                    WHEN 'APPLIES' THEN 4
                    ELSE 99
                  END,
                  CASE severity
                    WHEN 'CRITICAL' THEN 1
                    WHEN 'HIGH' THEN 2
                    WHEN 'MEDIUM' THEN 3
                    WHEN 'LOW' THEN 4
                    ELSE 99
                  END,
                  recommended_action
                LIMIT 5
            """),
            {"analysis_id": analysis_id},
        ).all()

        seen = set()
        actions: list[str] = []
        for row in rows:
            if row.recommended_action not in seen:
                seen.add(row.recommended_action)
                actions.append(row.recommended_action)
        return actions

    def get_overview_supporting_lists(self, db: Session, analysis_id: str) -> dict:
        assumptions = db.execute(
            text("""
                SELECT DISTINCT assumptions_text
                FROM analysis_findings
                WHERE analysis_id = :analysis_id
                AND assumptions_text IS NOT NULL
                AND assumptions_text <> ''
                ORDER BY assumptions_text
            """),
            {"analysis_id": analysis_id},
        ).all()

        missing_inputs = db.execute(
            text("""
                SELECT DISTINCT missing_inputs_text
                FROM analysis_findings
                WHERE analysis_id = :analysis_id
                AND missing_inputs_text IS NOT NULL
                AND missing_inputs_text <> ''
                ORDER BY missing_inputs_text
            """),
            {"analysis_id": analysis_id},
        ).all()

        derived_risks: list[str] = []
        if any(row.missing_inputs_text for row in missing_inputs):
            derived_risks.append("Analysis includes findings with incomplete customer context.")

        return {
            "assumptions": [row.assumptions_text for row in assumptions],
            "missing_inputs": [row.missing_inputs_text for row in missing_inputs],
            "derived_risks": derived_risks,
        }