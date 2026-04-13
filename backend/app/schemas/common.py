from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    AnalysisStatus,
    ChangeTaxonomy,
    EnvironmentType,
    FindingStatus,
    ImpactType,
    ReviewStatus,
    Severity,
)


class APIStatusResponse(BaseModel):
    status: str

    model_config = ConfigDict(use_enum_values=True)


class EnumCatalogResponse(BaseModel):
    analysis_statuses: list[AnalysisStatus]
    finding_statuses: list[FindingStatus]
    review_statuses: list[ReviewStatus]
    change_taxonomies: list[ChangeTaxonomy]
    severities: list[Severity]
    impact_types: list[ImpactType]
    environment_types: list[EnvironmentType]

    model_config = ConfigDict(use_enum_values=True)