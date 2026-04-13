from app.core.enums import (
    AnalysisStatus,
    ChangeTaxonomy,
    EnvironmentType,
    FindingStatus,
    ImpactType,
    ReviewStatus,
    Severity,
)

API_V1_PREFIX = "/api/v1"

ANALYSIS_TERMINAL_STATUSES: tuple[AnalysisStatus, ...] = (
    AnalysisStatus.READY,
    AnalysisStatus.ARCHIVED,
    AnalysisStatus.FAILED,
)

ANALYSIS_INTERRUPT_STATUSES: tuple[AnalysisStatus, ...] = (
    AnalysisStatus.BLOCKED,
    AnalysisStatus.FAILED,
    AnalysisStatus.STALE,
    AnalysisStatus.REQUIRES_REFRESH,
)

ANALYSIS_ACTIVE_STATUSES: tuple[AnalysisStatus, ...] = (
    AnalysisStatus.DRAFT,
    AnalysisStatus.INTAKE_VALIDATED,
    AnalysisStatus.ANALYSIS_RUNNING,
    AnalysisStatus.ANALYSIS_COMPLETE,
    AnalysisStatus.REVIEW_REQUIRED,
)

VALID_ANALYSIS_STATUSES: tuple[str, ...] = tuple(status.value for status in AnalysisStatus)
VALID_FINDING_STATUSES: tuple[str, ...] = tuple(status.value for status in FindingStatus)
VALID_REVIEW_STATUSES: tuple[str, ...] = tuple(status.value for status in ReviewStatus)
VALID_CHANGE_TAXONOMIES: tuple[str, ...] = tuple(value.value for value in ChangeTaxonomy)
VALID_SEVERITIES: tuple[str, ...] = tuple(value.value for value in Severity)
VALID_IMPACT_TYPES: tuple[str, ...] = tuple(value.value for value in ImpactType)
VALID_ENVIRONMENT_TYPES: tuple[str, ...] = tuple(value.value for value in EnvironmentType)