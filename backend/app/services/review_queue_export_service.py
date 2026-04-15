import csv
import io

from sqlalchemy.orm import Session

from app.repositories.review_queue_repository import ReviewQueueRepository


class ReviewQueueExportService:
    def __init__(self) -> None:
        self.repository = ReviewQueueRepository()

    def export_csv(self, db: Session) -> str:
        rows = self.repository.get_open_review_items(db)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "review_item_id",
            "finding_id",
            "analysis_id",
            "application_name",
            "finding_headline",
            "kb_reference",
            "review_reason",
            "assigned_owner_user_id",
            "due_date",
            "review_status",
            "created_utc",
            "updated_utc",
            "resolution_note",
            "defer_reason",
            "is_overdue",
        ])

        for row in rows:
            writer.writerow([
                row["review_item_id"],
                row["finding_id"],
                row["analysis_id"],
                row["application_name"],
                row["finding_headline"],
                row["kb_reference"],
                row["review_reason"],
                row["assigned_owner_user_id"],
                row["due_date"],
                row["review_status"],
                row["created_utc"],
                row["updated_utc"],
                row["resolution_note"] or "",
                row["defer_reason"] or "",
                "true" if row["is_overdue"] else "false",
            ])

        return output.getvalue()