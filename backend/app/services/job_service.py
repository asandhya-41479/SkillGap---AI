from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import JobDescription
from app.schemas.job import JobCreate


def create_job(db: Session, user_id: int, job_in: JobCreate) -> JobDescription:
    job = JobDescription(user_id=user_id, **job_in.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_user_jobs(db: Session, user_id: int) -> list[JobDescription]:
    return (
        db.query(JobDescription)
        .filter(JobDescription.user_id == user_id)
        .order_by(JobDescription.created_at.desc())
        .all()
    )


def get_owned_job(db: Session, user_id: int, job_id: int) -> JobDescription:
    job = (
        db.query(JobDescription)
        .filter(JobDescription.id == job_id, JobDescription.user_id == user_id)
        .first()
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")

    return job


def delete_job(db: Session, user_id: int, job_id: int) -> None:
    job = get_owned_job(db, user_id, job_id)
    db.delete(job)
    db.commit()