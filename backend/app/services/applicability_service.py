from app.core.enums import ReportStatus
from app.services.versioning import version_in_window


class ApplicabilityService:
    def evaluate(
        self,
        customer_application: dict,
        customer_modules: list[str],
        change_record: dict,
        has_customizations: bool | None,
        has_integrations: bool | None,
        kb_provenance_present: bool,
    ) -> tuple[str, str]:
        if not kb_provenance_present:
            return ReportStatus.BLOCKED.value, "Required KB provenance is missing."

        if change_record["application_name"] != customer_application["application_name"]:
            return ReportStatus.DOES_NOT_APPLY.value, "Application does not match."

        if not version_in_window(
            current_version=customer_application["current_version"],
            target_version=customer_application["target_version"],
            version_from=change_record.get("version_from"),
            version_to=change_record.get("version_to"),
        ):
            return ReportStatus.DOES_NOT_APPLY.value, "Version window does not match."

        change_module = change_record.get("module_name")
        if change_module and change_module not in customer_modules:
            return ReportStatus.DOES_NOT_APPLY.value, "Required module is not enabled."

        if change_record.get("customization_review_required"):
            if has_customizations is None:
                return ReportStatus.UNKNOWN.value, "Customization data is missing."
            if has_customizations:
                return ReportStatus.REQUIRES_REVIEW.value, "Customization review is required."

        if change_record.get("integration_review_required"):
            if has_integrations is None:
                return ReportStatus.UNKNOWN.value, "Integration data is missing."
            if has_integrations:
                return ReportStatus.REQUIRES_REVIEW.value, "Integration review is required."

        return ReportStatus.APPLIES.value, "Application, version, and module match."