from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.readiness import ReadinessResponse
from app.services import readiness_service as svc

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.post("/{analysis_id}/calculate", response_model=ReadinessResponse, status_code=status.HTTP_201_CREATED)
def calculate(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Compute the score now and save it (one snapshot per analysis per day; same-day calls update it)."""
    return svc.to_response(db, user.id, svc.calculate(db, user.id, analysis_id))


@router.get("/{analysis_id}", response_model=ReadinessResponse)
def get_readiness(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Latest saved score with a live breakdown; is_stale=true means inputs changed since it was calculated."""
    return svc.to_response(db, user.id, svc.latest(db, user.id, analysis_id))