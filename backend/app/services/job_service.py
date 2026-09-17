from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import JobDescription, JobRequirement, JobStatus
from app.schemas.job import JobCreate
from app.services.gemini_service import extract_requirements
from app.services.requirement_processor import process_extraction


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


def analyze_job(db: Session, user_id: int, job_id: int) -> JobDescription:
    job = get_owned_job(db, user_id, job_id)

    try:
        raw_items = extract_requirements(job.raw_description)
        processed = process_extraction(raw_items)
    except HTTPException:
        job.status = JobStatus.failed
        db.commit()
        raise

    db.query(JobRequirement).filter(JobRequirement.job_description_id == job.id).delete()

    for item in processed:
        db.add(JobRequirement(
            job_description_id=job.id,
            skill_name=item["skill_name"],
            category=item["category"],
            importance=item["importance"],
            source="gemini",
        ))

    job.status = JobStatus.analyzed
    db.commit()
    db.refresh(job)
    return job