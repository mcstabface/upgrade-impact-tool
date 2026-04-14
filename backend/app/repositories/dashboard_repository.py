from sqlalchemy import text
from sqlalchemy.orm import Session


class DashboardRepository:
    def get_dashboard(self, db: Session) -> list[dict]:
        query = text("""
            SELECT
                ar.analysis_id,
                c.customer_name,
                e.environment_name,
                ar.completed_utc AS analysis_date,
                ar.overall_status,
                COUNT(aa.analysis_application_id) AS applications_count,
                ar.applies_count,
                ar.review_required_count,
                ar.unknown_count,
                ar.blocked_count
            FROM analysis_runs ar
            JOIN customers c ON c.customer_id = ar.customer_id
            JOIN environments e ON e.environment_id = ar.environment_id
            LEFT JOIN analysis_applications aa ON aa.analysis_id = ar.analysis_id
            GROUP BY
                ar.analysis_id, c.customer_name, e.environment_name, ar.completed_utc,
                ar.overall_status, ar.applies_count, ar.review_required_count,
                ar.unknown_count, ar.blocked_count
            ORDER BY ar.completed_utc DESC NULLS LAST, ar.analysis_id
        """)
        return [dict(row._mapping) for row in db.execute(query).all()]

    def get_top_risks(self, db: Session) -> list[str]:
        query = text("""
            SELECT af.headline
            FROM analysis_findings af
            JOIN analysis_runs ar ON ar.analysis_id = af.analysis_id
            WHERE af.finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN')
            ORDER BY
            CASE af.finding_status
                WHEN 'BLOCKED' THEN 1
                WHEN 'REQUIRES_REVIEW' THEN 2
                WHEN 'UNKNOWN' THEN 3
                ELSE 99
            END,
            CASE af.severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 99
            END,
            af.headline
            LIMIT 5
        """)
        rows = db.execute(query).all()
        return [row.headline for row in rows]

    def get_top_actions(self, db: Session) -> list[str]:
        query = text("""
            SELECT af.recommended_action
            FROM analysis_findings af
            WHERE af.finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN', 'APPLIES')
            AND af.recommended_action IS NOT NULL
            AND af.recommended_action <> ''
            ORDER BY
            CASE af.finding_status
                WHEN 'BLOCKED' THEN 1
                WHEN 'REQUIRES_REVIEW' THEN 2
                WHEN 'UNKNOWN' THEN 3
                WHEN 'APPLIES' THEN 4
                ELSE 99
            END,
            CASE af.severity
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                WHEN 'LOW' THEN 4
                ELSE 99
            END,
            af.recommended_action
            LIMIT 5
        """)
        rows = db.execute(query).all()

        seen = set()
        actions = []
        for row in rows:
            if row.recommended_action not in seen:
                seen.add(row.recommended_action)
                actions.append(row.recommended_action)
        return actions