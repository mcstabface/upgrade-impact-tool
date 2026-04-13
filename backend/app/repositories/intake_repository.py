from sqlalchemy import text
from sqlalchemy.orm import Session


class IntakeRepository:
    def create_draft(
        self,
        db: Session,
        intake_id: str,
        customer_name: str,
        environment_name: str,
        environment_type: str,
        status: str,
        payload_json: dict,
        created_utc: int,
    ) -> None:
        query = text("""
            INSERT INTO intake_drafts (
                intake_id, customer_name, environment_name, environment_type,
                status, payload_json, completeness_score, created_utc, updated_utc
            ) VALUES (
                :intake_id, :customer_name, :environment_name, :environment_type,
                :status, CAST(:payload_json AS jsonb), 0, :created_utc, :created_utc
            )
        """)
        db.execute(
            query,
            {
                "intake_id": intake_id,
                "customer_name": customer_name,
                "environment_name": environment_name,
                "environment_type": environment_type,
                "status": status,
                "payload_json": __import__("json").dumps(payload_json),
                "created_utc": created_utc,
            },
        )
        db.commit()

    def get_draft(self, db: Session, intake_id: str) -> dict | None:
        query = text("""
            SELECT
                intake_id,
                customer_name,
                environment_name,
                environment_type,
                status,
                payload_json,
                completeness_score,
                created_utc,
                updated_utc
            FROM intake_drafts
            WHERE intake_id = :intake_id
        """)
        row = db.execute(query, {"intake_id": intake_id}).first()
        return dict(row._mapping) if row else None

    def update_draft(
        self,
        db: Session,
        intake_id: str,
        status: str,
        payload_json: dict,
        completeness_score: int,
        updated_utc: int,
    ) -> None:
        query = text("""
            UPDATE intake_drafts
            SET
                status = :status,
                payload_json = CAST(:payload_json AS jsonb),
                completeness_score = :completeness_score,
                updated_utc = :updated_utc
            WHERE intake_id = :intake_id
        """)
        db.execute(
            query,
            {
                "intake_id": intake_id,
                "status": status,
                "payload_json": __import__("json").dumps(payload_json),
                "completeness_score": completeness_score,
                "updated_utc": updated_utc,
            },
        )
        db.commit()

    def create_analysis_run(
        self,
        db: Session,
        analysis_id: str,
        customer_id: int,
        environment_id: int,
        snapshot_id: int,
        status: str,
        started_utc: int,
    ) -> None:
        query = text("""
            INSERT INTO analysis_runs (
                analysis_id, customer_id, environment_id, snapshot_id,
                kb_catalog_version, analysis_status, overall_status,
                applies_count, review_required_count, unknown_count, blocked_count,
                assumptions_count, missing_inputs_count, derived_risks_count,
                started_utc, completed_utc, duration_ms, created_by_user_id
            ) VALUES (
                :analysis_id, :customer_id, :environment_id, :snapshot_id,
                NULL, :status, :status,
                0, 0, 0, 0,
                0, 0, 0,
                :started_utc, NULL, NULL, 'system'
            )
        """)
        db.execute(
            query,
            {
                "analysis_id": analysis_id,
                "customer_id": customer_id,
                "environment_id": environment_id,
                "snapshot_id": snapshot_id,
                "status": status,
                "started_utc": started_utc,
            },
        )

    def create_state_transition(
        self,
        db: Session,
        analysis_id: str,
        previous_state: str | None,
        new_state: str,
        trigger_event: str,
        transition_utc: int,
    ) -> None:
        query = text("""
            INSERT INTO state_transitions (
                analysis_id, previous_state, new_state,
                trigger_event, user_id, transition_utc
            ) VALUES (
                :analysis_id, :previous_state, :new_state,
                :trigger_event, 'system', :transition_utc
            )
        """)
        db.execute(
            query,
            {
                "analysis_id": analysis_id,
                "previous_state": previous_state,
                "new_state": new_state,
                "trigger_event": trigger_event,
                "transition_utc": transition_utc,
            },
        )

    def commit(self, db: Session) -> None:
        db.commit()