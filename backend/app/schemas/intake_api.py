from pydantic import BaseModel, Field

from app.core.enums import AnalysisStatus, EnvironmentType


class IntakeCreateRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    environment_name: str = Field(min_length=1)
    environment_type: EnvironmentType


class IntakeCreateResponse(BaseModel):
    intake_id: str
    status: str
    created_utc: int


class IntakeUpdateRequest(BaseModel):
    applications: list[dict] | None = None
    primary_technical_contact: dict | None = None
    primary_business_contact: dict | None = None
    environment_count: int | None = None
    environment_classification: list[str] | None = None
    upgrade_sequence: list[str] | None = None
    vendor_kb_documents: list[dict] | None = None
    customizations: list[dict] | None = None
    integrations: list[dict] | None = None
    jobs: list[dict] | None = None


class IntakeUpdateResponse(BaseModel):
    intake_id: str
    status: str
    completeness_score: int


class IntakeDetailResponse(BaseModel):
    intake_id: str
    status: str
    customer_name: str
    environment_name: str
    environment_type: str
    applications: list[dict] = []


class IntakeValidateResponse(BaseModel):
    intake_id: str
    status: str
    completeness_score: int | None = None
    missing_required_fields: list[str] = []
    warnings: list[str] = []


class StartAnalysisRequest(BaseModel):
    run_mode: str = "STANDARD"


class StartAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    started_utc: int