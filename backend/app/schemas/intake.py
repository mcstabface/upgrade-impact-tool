from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.enums import (
    AnalysisStatus,
    CriticalityLevel,
    CustomizationObjectType,
    CustomerEnvironmentType,
    IntegrationInterfaceType,
    JobType,
)


class ContactInfo(BaseModel):
    name: str = Field(min_length=1)
    email: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class ModuleEnabled(BaseModel):
    module_name: str = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class ApplicationInScope(BaseModel):
    application_name: str = Field(min_length=1)
    product_line: str = Field(min_length=1)
    current_version: str = Field(min_length=1)
    target_version: str = Field(min_length=1)
    modules_enabled: list[ModuleEnabled] = Field(min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class CustomizationItem(BaseModel):
    object_name: str = Field(min_length=1)
    object_type: CustomizationObjectType
    description: str | None = None
    owning_team: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class IntegrationItem(BaseModel):
    integration_name: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    target_system: str = Field(min_length=1)
    interface_type: IntegrationInterfaceType
    schedule: str | None = None
    criticality: CriticalityLevel | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class JobItem(BaseModel):
    job_name: str = Field(min_length=1)
    job_type: JobType
    schedule: str | None = None
    owner: str | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class VendorKnowledgeBaseDocument(BaseModel):
    article_number: str = Field(min_length=1)
    title: str = Field(min_length=1)
    publication_date: str = Field(min_length=1)
    source_link: HttpUrl

    model_config = ConfigDict(str_strip_whitespace=True)


class IntakeRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    environment_name: str = Field(min_length=1)
    environment_type: CustomerEnvironmentType

    primary_technical_contact: ContactInfo
    primary_business_contact: ContactInfo

    applications: list[ApplicationInScope] = Field(min_length=1)

    environment_count: int = Field(ge=1)
    environment_classification: list[str] = Field(min_length=1)
    upgrade_sequence: list[str] | None = None

    vendor_kb_documents: list[VendorKnowledgeBaseDocument] = Field(min_length=1)

    customizations: list[CustomizationItem] | None = None
    integrations: list[IntegrationItem] | None = None
    jobs: list[JobItem] | None = None

    @field_validator("environment_classification")
    @classmethod
    def validate_environment_classification(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().upper() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("environment_classification must not be empty")
        return cleaned

    model_config = ConfigDict(str_strip_whitespace=True)


class IntakeCreateResponse(BaseModel):
    analysis_id: str
    analysis_status: AnalysisStatus
    warnings: list[str]
    applications_in_scope: int
    environment_count: int

    model_config = ConfigDict(use_enum_values=True)