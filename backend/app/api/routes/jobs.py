from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.job import JobCreate, JobDetail, JobListItem, JobRequirementResponse
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobDetail, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return job_service.create_job(db, current_user.id, job_in)


@router.get("", response_model=list[JobListItem])
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return job_service.get_user_jobs(db, current_user.id)


@router.get("/{job_id}", response_model=JobDetail)
def get_job(
    job_id: int,

    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return job_service.get_owned_job(db, current_user.id, job_id)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job_service.delete_job(db, current_user.id, job_id)


@router.post("/{job_id}/analyze", response_model=JobDetail)
def analyze_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return job_service.analyze_job(db, current_user.id, job_id)


@router.get("/{job_id}/requirements", response_model=list[JobRequirementResponse])
def get_job_requirements(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = job_service.get_owned_job(db, current_user.id, job_id)
    return job.requirements