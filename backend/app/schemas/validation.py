from pydantic import BaseModel


class IntakeValidationResult(BaseModel):
    status: str
    completeness_score: int
    missing_required_fields: list[str]
    warnings: list[str]