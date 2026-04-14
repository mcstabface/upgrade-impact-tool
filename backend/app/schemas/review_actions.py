from pydantic import BaseModel


class ResolveFindingRequest(BaseModel):
    resolution_note: str


class ResolveFindingResponse(BaseModel):
    finding_id: int
    finding_status: str
    resolution_note: str