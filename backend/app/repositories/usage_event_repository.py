import json

from sqlalchemy import text
from sqlalchemy.orm import Session


class UsageEventRepository:
    def create_event(
        self,
        db: Session,
        *,
        event_type: str,
        actor_role: str,
        actor_user_id: str | None,
        entity_type: str,
        entity_id: str,
        related_analysis_id: str | None,
        event_payload: dict | None,
        created_utc: int,
    ) -> None:
        query = text(
            """
            INSERT INTO usage_events (
                event_type,
                actor_role,
                actor_user_id,
                entity_type,
                entity_id,
                related_analysis_id,
                event_payload,
                created_utc
            ) VALUES (
                :event_type,
                :actor_role,
                :actor_user_id,
                :entity_type,
                :entity_id,
                :related_analysis_id,
                CAST(:event_payload AS json),
                :created_utc
            )
            """
        )
        db.execute(
            query,
            {
                "event_type": event_type,
                "actor_role": actor_role,
                "actor_user_id": actor_user_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "related_analysis_id": related_analysis_id,
                "event_payload": json.dumps(event_payload or {}),
                "created_utc": created_utc,
            },
        )