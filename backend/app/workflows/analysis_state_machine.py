from app.core.enums import AnalysisStatus


ALLOWED_STATE_TRANSITIONS: dict[AnalysisStatus, set[AnalysisStatus]] = {
    AnalysisStatus.DRAFT: {
        AnalysisStatus.INTAKE_VALIDATED,
        AnalysisStatus.BLOCKED,
        AnalysisStatus.FAILED,
    },
    AnalysisStatus.INTAKE_VALIDATED: {
        AnalysisStatus.ANALYSIS_RUNNING,
        AnalysisStatus.BLOCKED,
        AnalysisStatus.FAILED,
        AnalysisStatus.DRAFT,
    },
    AnalysisStatus.ANALYSIS_RUNNING: {
        AnalysisStatus.ANALYSIS_COMPLETE,
        AnalysisStatus.FAILED,
        AnalysisStatus.BLOCKED,
    },
    AnalysisStatus.ANALYSIS_COMPLETE: {
        AnalysisStatus.REVIEW_REQUIRED,
        AnalysisStatus.READY,
        AnalysisStatus.FAILED,
    },
    AnalysisStatus.REVIEW_REQUIRED: {
        AnalysisStatus.READY,
        AnalysisStatus.FAILED,
        AnalysisStatus.BLOCKED,
    },
    AnalysisStatus.READY: {
        AnalysisStatus.ARCHIVED,
        AnalysisStatus.STALE,
    },
    AnalysisStatus.STALE: {
        AnalysisStatus.REQUIRES_REFRESH,
        AnalysisStatus.ARCHIVED,
    },
    AnalysisStatus.REQUIRES_REFRESH: {
        AnalysisStatus.ANALYSIS_RUNNING,
        AnalysisStatus.ARCHIVED,
    },
    AnalysisStatus.BLOCKED: {
        AnalysisStatus.DRAFT,
        AnalysisStatus.INTAKE_VALIDATED,
        AnalysisStatus.ANALYSIS_RUNNING,
    },
    AnalysisStatus.FAILED: {
        AnalysisStatus.ANALYSIS_RUNNING,
        AnalysisStatus.ARCHIVED,
    },
    AnalysisStatus.ARCHIVED: set(),
}


def can_transition(previous_state: AnalysisStatus, new_state: AnalysisStatus) -> bool:
    return new_state in ALLOWED_STATE_TRANSITIONS.get(previous_state, set())