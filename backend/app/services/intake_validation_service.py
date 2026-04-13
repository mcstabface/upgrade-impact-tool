from app.core.enums import AnalysisStatus
from app.schemas.validation import IntakeValidationResult


class IntakeValidationService:
    def validate(self, payload: dict) -> IntakeValidationResult:
        missing_required_fields: list[str] = []
        warnings: list[str] = []

        if not payload.get("customer_name"):
            missing_required_fields.append("customer_name")
        if not payload.get("environment_name"):
            missing_required_fields.append("environment_name")
        if not payload.get("environment_type"):
            missing_required_fields.append("environment_type")

        applications = payload.get("applications") or []
        if not applications:
            missing_required_fields.append("applications")

        for idx, app in enumerate(applications):
            prefix = f"applications[{idx}]"
            if not app.get("application_name"):
                missing_required_fields.append(f"{prefix}.application_name")
            if not app.get("current_version"):
                missing_required_fields.append(f"{prefix}.current_version")
            if not app.get("target_version"):
                missing_required_fields.append(f"{prefix}.target_version")

            modules = app.get("modules_enabled") or []
            if not modules:
                missing_required_fields.append(f"{prefix}.modules_enabled")

        if not payload.get("primary_technical_contact"):
            warnings.append("No technical contact provided")
        if not payload.get("primary_business_contact"):
            warnings.append("No business contact provided")
        if not payload.get("integrations"):
            warnings.append("No integration inventory provided")
        if not payload.get("customizations"):
            warnings.append("No customization inventory provided")
        if not payload.get("jobs"):
            warnings.append("Job inventory is incomplete or not provided")

        completeness_score = self._calculate_completeness(payload)

        status = (
            AnalysisStatus.BLOCKED.value
            if missing_required_fields
            else AnalysisStatus.INTAKE_VALIDATED.value
        )

        return IntakeValidationResult(
            status=status,
            completeness_score=completeness_score,
            missing_required_fields=sorted(set(missing_required_fields)),
            warnings=warnings,
        )

    def _calculate_completeness(self, payload: dict) -> int:
        checks = [
            bool(payload.get("customer_name")),
            bool(payload.get("environment_name")),
            bool(payload.get("environment_type")),
            bool(payload.get("applications")),
            bool(payload.get("primary_technical_contact")),
            bool(payload.get("primary_business_contact")),
            bool(payload.get("integrations")),
            bool(payload.get("customizations")),
            bool(payload.get("jobs")),
        ]
        return int(round((sum(1 for item in checks if item) / len(checks)) * 100))