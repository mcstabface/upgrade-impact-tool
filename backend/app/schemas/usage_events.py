from pydantic import BaseModel, Field


class ResultsOverviewSessionEventRequest(BaseModel):
    analysis_id: str
    duration_seconds: int = Field(ge=1)