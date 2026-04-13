from fastapi import APIRouter

from app.core.enums import (
    AnalysisStatus,
    ChangeTaxonomy,
    EnvironmentType,
    FindingStatus,
    ImpactType,
    ReviewStatus,
    Severity,
)
from app.schemas.common import EnumCatalogResponse

router = APIRouter(tags=["meta"])


@router.get("/meta/enums", response_model=EnumCatalogResponse)
def get_enum_catalog() -> EnumCatalogResponse:
    return EnumCatalogResponse(
        analysis_statuses=list(AnalysisStatus),
        finding_statuses=list(FindingStatus),
        review_statuses=list(ReviewStatus),
        change_taxonomies=list(ChangeTaxonomy),
        severities=list(Severity),
        impact_types=list(ImpactType),
        environment_types=list(EnvironmentType),
    )