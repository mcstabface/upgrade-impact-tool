import hashlib
import json
import time

from sqlalchemy import text
from sqlalchemy.orm import Session


class SnapshotService:
    def build_snapshot_payload(self, draft: dict) -> dict:
        payload = draft.get("payload_json") or {}
        return {
            "customer_name": draft["customer_name"],
            "environment_name": draft["environment_name"],
            "environment_type": draft["environment_type"],
            "applications": payload.get("applications", []),
            "primary_technical_contact": payload.get("primary_technical_contact"),
            "primary_business_contact": payload.get("primary_business_contact"),
            "environment_count": payload.get("environment_count"),
            "environment_classification": payload.get("environment_classification"),
            "upgrade_sequence": payload.get("upgrade_sequence"),
            "vendor_kb_documents": payload.get("vendor_kb_documents"),
            "customizations": payload.get("customizations"),
            "integrations": payload.get("integrations"),
            "jobs": payload.get("jobs"),
        }

    def compute_content_hash(self, snapshot_payload: dict) -> str:
        canonical = json.dumps(snapshot_payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def persist_snapshot_for_intake(
        self,
        db: Session,
        intake_row: dict,
    ) -> tuple[int, str]:
        snapshot_payload = self.build_snapshot_payload(intake_row)
        content_hash = self.compute_content_hash(snapshot_payload)
        created_utc = int(time.time())

        customer_id = self._get_or_create_customer(
            db=db,
            customer_name=intake_row["customer_name"],
            created_utc=created_utc,
        )

        environment_id = self._get_or_create_environment(
            db=db,
            customer_id=customer_id,
            environment_name=intake_row["environment_name"],
            environment_type=intake_row["environment_type"],
            created_utc=created_utc,
        )

        existing = db.execute(
            text("""
                SELECT snapshot_id
                FROM customer_state_snapshots
                WHERE customer_id = :customer_id
                  AND environment_id = :environment_id
                  AND content_hash = :content_hash
                ORDER BY snapshot_version DESC
                LIMIT 1
            """),
            {
                "customer_id": customer_id,
                "environment_id": environment_id,
                "content_hash": content_hash,
            },
        ).first()

        if existing:
            return existing.snapshot_id, content_hash

        current_version_row = db.execute(
            text("""
                SELECT COALESCE(MAX(snapshot_version), 0) AS max_version
                FROM customer_state_snapshots
                WHERE customer_id = :customer_id
                  AND environment_id = :environment_id
            """),
            {
                "customer_id": customer_id,
                "environment_id": environment_id,
            },
        ).first()

        next_version = int(current_version_row.max_version) + 1

        db.execute(
            text("""
                UPDATE customer_state_snapshots
                SET is_active = false
                WHERE customer_id = :customer_id
                  AND environment_id = :environment_id
                  AND is_active = true
            """),
            {
                "customer_id": customer_id,
                "environment_id": environment_id,
            },
        )

        snapshot_row = db.execute(
            text("""
                INSERT INTO customer_state_snapshots (
                    customer_id,
                    environment_id,
                    snapshot_version,
                    snapshot_status,
                    source_type,
                    completeness_score,
                    created_utc,
                    created_by_user_id,
                    content_hash,
                    is_active
                ) VALUES (
                    :customer_id,
                    :environment_id,
                    :snapshot_version,
                    'ACTIVE',
                    'INTAKE',
                    :completeness_score,
                    :created_utc,
                    'system',
                    :content_hash,
                    true
                )
                RETURNING snapshot_id
            """),
            {
                "customer_id": customer_id,
                "environment_id": environment_id,
                "snapshot_version": next_version,
                "completeness_score": intake_row["completeness_score"],
                "created_utc": created_utc,
                "content_hash": content_hash,
            },
        ).first()

        snapshot_id = snapshot_row.snapshot_id

        applications = snapshot_payload.get("applications") or []
        for application in applications:
            app_row = db.execute(
                text("""
                    INSERT INTO customer_applications (
                        snapshot_id,
                        application_name,
                        product_line,
                        current_version,
                        target_version,
                        application_status
                    ) VALUES (
                        :snapshot_id,
                        :application_name,
                        :product_line,
                        :current_version,
                        :target_version,
                        'IN_SCOPE'
                    )
                    RETURNING customer_application_id
                """),
                {
                    "snapshot_id": snapshot_id,
                    "application_name": application["application_name"],
                    "product_line": application.get("product_line", "UNKNOWN"),
                    "current_version": application["current_version"],
                    "target_version": application["target_version"],
                },
            ).first()

            customer_application_id = app_row.customer_application_id

            modules = application.get("modules_enabled") or []
            for module_name in modules:
                if isinstance(module_name, dict):
                    module_name = module_name.get("module_name")
                if not module_name:
                    continue

                db.execute(
                    text("""
                        INSERT INTO customer_modules (
                            customer_application_id,
                            module_name
                        ) VALUES (
                            :customer_application_id,
                            :module_name
                        )
                    """),
                    {
                        "customer_application_id": customer_application_id,
                        "module_name": module_name,
                    },
                )

        return snapshot_id, content_hash

    def _get_or_create_customer(
        self,
        db: Session,
        customer_name: str,
        created_utc: int,
    ) -> int:
        row = db.execute(
            text("""
                SELECT customer_id
                FROM customers
                WHERE customer_name = :customer_name
                LIMIT 1
            """),
            {"customer_name": customer_name},
        ).first()

        if row:
            return row.customer_id

        row = db.execute(
            text("""
                INSERT INTO customers (
                    customer_name,
                    status,
                    created_utc,
                    updated_utc
                ) VALUES (
                    :customer_name,
                    'ACTIVE',
                    :created_utc,
                    :created_utc
                )
                RETURNING customer_id
            """),
            {
                "customer_name": customer_name,
                "created_utc": created_utc,
            },
        ).first()

        return row.customer_id

    def _get_or_create_environment(
        self,
        db: Session,
        customer_id: int,
        environment_name: str,
        environment_type: str,
        created_utc: int,
    ) -> int:
        row = db.execute(
            text("""
                SELECT environment_id
                FROM environments
                WHERE customer_id = :customer_id
                  AND environment_name = :environment_name
                LIMIT 1
            """),
            {
                "customer_id": customer_id,
                "environment_name": environment_name,
            },
        ).first()

        if row:
            return row.environment_id

        row = db.execute(
            text("""
                INSERT INTO environments (
                    customer_id,
                    environment_name,
                    environment_type,
                    status,
                    created_utc,
                    updated_utc
                ) VALUES (
                    :customer_id,
                    :environment_name,
                    :environment_type,
                    'ACTIVE',
                    :created_utc,
                    :created_utc
                )
                RETURNING environment_id
            """),
            {
                "customer_id": customer_id,
                "environment_name": environment_name,
                "environment_type": environment_type,
                "created_utc": created_utc,
            },
        ).first()

        return row.environment_id