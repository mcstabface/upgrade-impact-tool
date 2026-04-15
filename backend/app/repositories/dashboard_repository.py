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
                ar.analysis_id,
                c.customer_name,
                e.environment_name,
                ar.completed_utc,
                ar.overall_status,
                ar.applies_count,
                ar.review_required_count,
                ar.unknown_count,
                ar.blocked_count
            ORDER BY ar.completed_utc DESC NULLS LAST, ar.analysis_id
        """)
        return [dict(row._mapping) for row in db.execute(query).all()]

    def get_top_risks(self, db: Session) -> list[str]:
        query = text("""
            WITH ranked_risks AS (
                SELECT
                    af.headline,
                    af.finding_status,
                    af.severity,
                    ROW_NUMBER() OVER (
                        PARTITION BY af.headline
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
                            af.finding_id DESC
                    ) AS rn
                FROM analysis_findings af
                WHERE af.finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN')
            )
            SELECT headline
            FROM ranked_risks
            WHERE rn = 1
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
        """)
        rows = db.execute(query).all()
        return [row.headline for row in rows]

    def get_review_item_summary(self, db: Session) -> dict:
        query = text("""
            SELECT
                COUNT(*) FILTER (WHERE review_status = 'OPEN') AS open_count,
                COUNT(*) FILTER (WHERE review_status = 'IN_PROGRESS') AS in_progress_count,
                COUNT(*) FILTER (WHERE review_status = 'DEFERRED') AS deferred_count,
                COUNT(*) FILTER (
                    WHERE review_status IN ('OPEN', 'IN_PROGRESS', 'DEFERRED')
                      AND due_date < CURRENT_DATE
                ) AS overdue_count
            FROM review_items
        """)
        row = db.execute(query).first()

        return {
            "open_count": row.open_count or 0,
            "in_progress_count": row.in_progress_count or 0,
            "deferred_count": row.deferred_count or 0,
            "overdue_count": row.overdue_count or 0,
        }

    def get_top_actions(self, db: Session) -> list[str]:
        query = text("""
            WITH ranked_actions AS (
                SELECT
                    af.recommended_action,
                    af.finding_status,
                    af.severity,
                    ROW_NUMBER() OVER (
                        PARTITION BY af.recommended_action
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
                            af.finding_id DESC
                    ) AS rn
                FROM analysis_findings af
                WHERE af.finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN', 'APPLIES')
                  AND af.recommended_action IS NOT NULL
                  AND af.recommended_action <> ''
            )
            SELECT recommended_action
            FROM ranked_actions
            WHERE rn = 1
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
        """)
        rows = db.execute(query).all()
        return [row.recommended_action for row in rows]