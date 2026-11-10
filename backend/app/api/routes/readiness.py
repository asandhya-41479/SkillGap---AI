from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.readiness import ReadinessComparison, ReadinessHistory, ReadinessResponse
from app.services import readiness_service as svc

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("/compare", response_model=ReadinessComparison)
def compare_analyses(
    from_analysis_id: int = Query(...),
    to_analysis_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compares before vs after gap analyses for the same target job."""
    return svc.compare_analyses(db, user.id, from_analysis_id, to_analysis_id)


@router.get("/jobs/{job_id}/history", response_model=ReadinessHistory)
def get_job_history(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Historical timeline of readiness snapshots for a specific job."""
    return svc.get_history(db, user.id, job_id)


@router.get("/jobs/{job_id}/latest", response_model=ReadinessResponse)
def get_latest_for_job(
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Latest saved readiness score for a job."""
    return svc.to_response(db, user.id, svc.latest_for_job(db, user.id, job_id))


@router.post("/{analysis_id}/calculate", response_model=ReadinessResponse, status_code=status.HTTP_201_CREATED)
def calculate(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Compute the score now and save it (one snapshot per analysis per day; same-day calls update it)."""
    return svc.to_response(db, user.id, svc.calculate(db, user.id, analysis_id))


@router.get("/{analysis_id}", response_model=ReadinessResponse)
def get_readiness(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Latest saved score with a live breakdown; is_stale=true means inputs changed since it was calculated."""
    return svc.to_response(db, user.id, svc.latest(db, user.id, analysis_id))
