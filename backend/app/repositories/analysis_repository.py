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
                ar.blocked_count,
                ar.stale_reason,
                ar.stale_detected_utc,
                ar.previous_analysis_id
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
                  AND finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN', 'APPLIES')
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
                  AND finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN', 'APPLIES')
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
                  AND finding_status IN ('BLOCKED', 'REQUIRES_REVIEW', 'UNKNOWN')
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

    def get_staleness_context(self, db: Session, analysis_id: str) -> dict | None:
        query = text("""
            SELECT
                analysis_id,
                customer_id,
                environment_id,
                analysis_status,
                overall_status,
                snapshot_id,
                kb_catalog_version AS recorded_kb_catalog_hash,
                snapshot_hash AS recorded_snapshot_hash,
                analysis_input_hash AS recorded_analysis_input_hash,
                stale_reason,
                stale_detected_utc
            FROM analysis_runs
            WHERE analysis_id = :analysis_id
        """)
        row = db.execute(query, {"analysis_id": analysis_id}).first()
        return dict(row._mapping) if row else None

    def get_snapshot_hash(self, db: Session, snapshot_id: int) -> str | None:
        query = text("""
            SELECT content_hash
            FROM customer_state_snapshots
            WHERE snapshot_id = :snapshot_id
        """)
        row = db.execute(query, {"snapshot_id": snapshot_id}).first()
        return row.content_hash if row else None

    def get_current_kb_catalog_hash(self, db: Session) -> str:
        query = text("""
            SELECT
                COALESCE(
                    md5(
                        COALESCE(
                            string_agg(
                                ka.kb_article_number || ':' || kav.content_hash,
                                '|' ORDER BY ka.kb_article_number, kav.kb_article_version_id
                            ),
                            ''
                        )
                    ),
                    md5('')
                ) AS kb_catalog_hash
            FROM kb_article_versions kav
            JOIN kb_articles ka ON ka.kb_article_id = kav.kb_article_id
            WHERE kav.is_current = true
        """)
        row = db.execute(query).first()
        return row.kb_catalog_hash

    def mark_analysis_stale(
        self,
        db: Session,
        *,
        analysis_id: str,
        stale_reason: str,
        stale_detected_utc: int,
    ) -> None:
        query = text("""
            UPDATE analysis_runs
            SET
                analysis_status = 'STALE',
                overall_status = 'STALE',
                stale_reason = :stale_reason,
                stale_detected_utc = :stale_detected_utc
            WHERE analysis_id = :analysis_id
        """)
        db.execute(
            query,
            {
                "analysis_id": analysis_id,
                "stale_reason": stale_reason,
                "stale_detected_utc": stale_detected_utc,
            },
        )

    def insert_state_transition(
        self,
        db: Session,
        *,
        analysis_id: str,
        previous_state: str | None,
        new_state: str,
        trigger_event: str,
        user_id: str | None,
        transition_utc: int,
    ) -> None:
        query = text("""
            INSERT INTO state_transitions (
                analysis_id,
                previous_state,
                new_state,
                trigger_event,
                user_id,
                transition_utc
            ) VALUES (
                :analysis_id,
                :previous_state,
                :new_state,
                :trigger_event,
                :user_id,
                :transition_utc
            )
        """)
        db.execute(
            query,
            {
                "analysis_id": analysis_id,
                "previous_state": previous_state,
                "new_state": new_state,
                "trigger_event": trigger_event,
                "user_id": user_id,
                "transition_utc": transition_utc,
            },
        )

    def get_active_snapshot_for_customer_environment(
        self,
        db: Session,
        *,
        customer_id: int,
        environment_id: int,
    ) -> dict | None:
        query = text("""
            SELECT
                snapshot_id,
                content_hash
            FROM customer_state_snapshots
            WHERE customer_id = :customer_id
              AND environment_id = :environment_id
              AND is_active = true
            ORDER BY snapshot_version DESC
            LIMIT 1
        """)
        row = db.execute(
            query,
            {
                "customer_id": customer_id,
                "environment_id": environment_id,
            },
        ).first()
        return dict(row._mapping) if row else None

    def create_refresh_analysis_run(
        self,
        db: Session,
        *,
        analysis_id: str,
        previous_analysis_id: str,
        customer_id: int,
        environment_id: int,
        snapshot_id: int,
        kb_catalog_hash: str,
        snapshot_hash: str,
        analysis_input_hash: str,
        started_utc: int,
    ) -> None:
        query = text("""
            INSERT INTO analysis_runs (
                analysis_id,
                customer_id,
                environment_id,
                snapshot_id,
                previous_analysis_id,
                kb_catalog_version,
                snapshot_hash,
                analysis_input_hash,
                stale_reason,
                stale_detected_utc,
                analysis_status,
                overall_status,
                applies_count,
                review_required_count,
                unknown_count,
                blocked_count,
                assumptions_count,
                missing_inputs_count,
                derived_risks_count,
                started_utc,
                completed_utc,
                duration_ms,
                created_by_user_id
            ) VALUES (
                :analysis_id,
                :customer_id,
                :environment_id,
                :snapshot_id,
                :previous_analysis_id,
                :kb_catalog_hash,
                :snapshot_hash,
                :analysis_input_hash,
                NULL,
                NULL,
                'REQUIRES_REFRESH',
                'REQUIRES_REFRESH',
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                :started_utc,
                NULL,
                NULL,
                'system'
            )
        """)
        db.execute(
            query,
            {
                "analysis_id": analysis_id,
                "previous_analysis_id": previous_analysis_id,
                "customer_id": customer_id,
                "environment_id": environment_id,
                "snapshot_id": snapshot_id,
                "kb_catalog_hash": kb_catalog_hash,
                "snapshot_hash": snapshot_hash,
                "analysis_input_hash": analysis_input_hash,
                "started_utc": started_utc,
            },
        )

    def get_delta_pair(self, db: Session, analysis_id: str) -> dict | None:
        query = text("""
            SELECT
                analysis_id AS current_analysis_id,
                previous_analysis_id
            FROM analysis_runs
            WHERE analysis_id = :analysis_id
              AND previous_analysis_id IS NOT NULL
        """)
        row = db.execute(query, {"analysis_id": analysis_id}).first()
        return dict(row._mapping) if row else None

    def get_analysis_finding_projection(self, db: Session, analysis_id: str) -> list[dict]:
        query = text("""
            SELECT
                af.finding_id,
                af.change_id,
                aa.application_name,
                af.finding_status,
                af.severity,
                af.headline,
                af.recommended_action,
                MIN(fe.kb_article_number) AS kb_reference
            FROM analysis_findings af
            JOIN analysis_applications aa
              ON aa.analysis_application_id = af.analysis_application_id
            LEFT JOIN finding_evidence fe
              ON fe.finding_id = af.finding_id
            WHERE af.analysis_id = :analysis_id
            GROUP BY
                af.finding_id,
                af.change_id,
                aa.application_name,
                af.finding_status,
                af.severity,
                af.headline,
                af.recommended_action
            ORDER BY aa.application_name, af.change_id, af.finding_id
        """)
        return [dict(row._mapping) for row in db.execute(query, {"analysis_id": analysis_id}).all()]