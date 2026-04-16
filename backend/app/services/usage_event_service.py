import time

from sqlalchemy.orm import Session

from app.repositories.usage_event_repository import UsageEventRepository


class UsageEventService:
    def __init__(self) -> None:
        self.repository = UsageEventRepository()

    def record_event(
        self,
        db: Session,
        *,
        event_type: str,
        actor_role: str,
        actor_user_id: str | None = None,
        entity_type: str,
        entity_id: str,
        related_analysis_id: str | None = None,
        event_payload: dict | None = None,
        commit: bool = True,
    ) -> None:
        self.repository.create_event(
            db=db,
            event_type=event_type,
            actor_role=actor_role,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            related_analysis_id=related_analysis_id,
            event_payload=event_payload,
            created_utc=int(time.time()),
        )
        if commit:
            db.commit()