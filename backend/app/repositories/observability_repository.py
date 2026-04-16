from sqlalchemy import text
from sqlalchemy.orm import Session


class ObservabilityRepository:
    def get_system_counts(self, db: Session) -> dict:
        query = text(
            """
            SELECT
                (SELECT COUNT(*) FROM analysis_runs) AS total_analyses,
                (SELECT COUNT(*) FROM analysis_runs WHERE overall_status = 'STALE') AS stale_analyses,
                (
                    SELECT COUNT(*)
                    FROM analysis_runs
                    WHERE previous_analysis_id IS NOT NULL
                ) AS refreshed_analyses,
                (
                    SELECT COUNT(*)
                    FROM review_items
                    WHERE review_status IN ('OPEN', 'IN_PROGRESS', 'DEFERRED')
                ) AS active_review_items,
                (
                    SELECT COUNT(*)
                    FROM review_items
                    WHERE review_status IN ('OPEN', 'IN_PROGRESS', 'DEFERRED')
                      AND due_date < CURRENT_DATE
                ) AS overdue_review_items
            """
        )
        row = db.execute(query).first()
        return dict(row._mapping)

    def get_most_common_missing_inputs(self, db: Session) -> list[dict]:
        query = text(
            """
            SELECT
                missing_inputs_text AS label,
                COUNT(*) AS value
            FROM analysis_findings
            WHERE missing_inputs_text IS NOT NULL
              AND missing_inputs_text <> ''
            GROUP BY missing_inputs_text
            ORDER BY COUNT(*) DESC, missing_inputs_text
            LIMIT 5
            """
        )
        return [dict(row._mapping) for row in db.execute(query).all()]

    def get_most_frequent_review_reasons(self, db: Session) -> list[dict]:
        query = text(
            """
            SELECT
                review_reason AS label,
                COUNT(*) AS value
            FROM review_items
            WHERE review_reason IS NOT NULL
              AND review_reason <> ''
            GROUP BY review_reason
            ORDER BY COUNT(*) DESC, review_reason
            LIMIT 5
            """
        )
        return [dict(row._mapping) for row in db.execute(query).all()]