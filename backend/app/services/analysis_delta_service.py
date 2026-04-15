from sqlalchemy.orm import Session

from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisDeltaSummaryResponse


class AnalysisDeltaService:
    def __init__(self) -> None:
        self.repository = AnalysisRepository()

    def get_delta_summary(self, db: Session, analysis_id: str) -> AnalysisDeltaSummaryResponse | None:
        pair = self.repository.get_delta_pair(db, analysis_id)
        if not pair:
            return None

        previous_analysis_id = pair["previous_analysis_id"]
        current_analysis_id = pair["current_analysis_id"]

        previous_rows = self.repository.get_analysis_finding_projection(db, previous_analysis_id)
        current_rows = self.repository.get_analysis_finding_projection(db, current_analysis_id)

        previous_map = {
            (row["application_name"], row["change_id"]): row
            for row in previous_rows
        }
        current_map = {
            (row["application_name"], row["change_id"]): row
            for row in current_rows
        }

        keys = sorted(set(previous_map.keys()) | set(current_map.keys()))

        new_findings_count = 0
        resolved_findings_count = 0
        updated_findings_count = 0
        unchanged_findings_count = 0
        applications_impacted: set[str] = set()

        previous_kb_articles = {
            row["kb_reference"]
            for row in previous_rows
            if row["kb_reference"]
        }
        current_kb_articles = {
            row["kb_reference"]
            for row in current_rows
            if row["kb_reference"]
        }

        for key in keys:
            previous_row = previous_map.get(key)
            current_row = current_map.get(key)

            if previous_row is None and current_row is not None:
                new_findings_count += 1
                applications_impacted.add(current_row["application_name"])
                continue

            if previous_row is not None and current_row is None:
                resolved_findings_count += 1
                applications_impacted.add(previous_row["application_name"])
                continue

            assert previous_row is not None
            assert current_row is not None

            changed = (
                previous_row["finding_status"] != current_row["finding_status"]
                or previous_row["severity"] != current_row["severity"]
                or previous_row["headline"] != current_row["headline"]
                or previous_row["recommended_action"] != current_row["recommended_action"]
                or previous_row["kb_reference"] != current_row["kb_reference"]
            )

            if changed:
                updated_findings_count += 1
                applications_impacted.add(current_row["application_name"])
            else:
                unchanged_findings_count += 1

        new_kb_articles_count = len(current_kb_articles - previous_kb_articles)
        updated_kb_articles_count = 0

        impacted_list = sorted(applications_impacted)

        summary_lines = [
            f"New findings: {new_findings_count}",
            f"Resolved findings: {resolved_findings_count}",
            f"Updated findings: {updated_findings_count}",
            f"Unchanged findings: {unchanged_findings_count}",
            f"New KB articles represented: {new_kb_articles_count}",
            f"Updated KB articles represented: {updated_kb_articles_count}",
        ]

        if impacted_list:
            summary_lines.append(f"Applications impacted: {', '.join(impacted_list)}")
        else:
            summary_lines.append("Applications impacted: none")

        return AnalysisDeltaSummaryResponse(
            previous_analysis_id=previous_analysis_id,
            current_analysis_id=current_analysis_id,
            new_findings_count=new_findings_count,
            resolved_findings_count=resolved_findings_count,
            updated_findings_count=updated_findings_count,
            unchanged_findings_count=unchanged_findings_count,
            new_kb_articles_count=new_kb_articles_count,
            updated_kb_articles_count=updated_kb_articles_count,
            applications_impacted=impacted_list,
            summary_lines=summary_lines,
        )