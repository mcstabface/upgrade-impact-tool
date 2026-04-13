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