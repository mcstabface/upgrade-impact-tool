from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.finding import FindingDetailResponse
from app.services.finding_service import FindingService

router = APIRouter(tags=["findings"])
service = FindingService()


@router.get("/findings/{finding_id}", response_model=FindingDetailResponse)
def get_finding_detail(finding_id: int, db: Session = Depends(get_db)) -> FindingDetailResponse:
    result = service.get_finding_detail(db, finding_id)
    if not result:
        raise HTTPException(status_code=404, detail="Finding not found")
    return result