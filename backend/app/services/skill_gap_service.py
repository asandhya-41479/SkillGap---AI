from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.skill_gap import SkillGapAnalysis, SkillGapResult, AnalysisStatus
from app.services.explanation_service import generate_explanation
from app.services.job_service import get_owned_job
from app.services.skill_gap_engine import run_gap_analysis
from app.services.skill_service import get_user_skills


def _get_owned_analysis(db: Session, user_id: int, analysis_id: int) -> SkillGapAnalysis:
    analysis = (
        db.query(SkillGapAnalysis)
        .options(joinedload(SkillGapAnalysis.results))
        .filter(SkillGapAnalysis.id == analysis_id, SkillGapAnalysis.user_id == user_id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    return analysis


def run_and_store_analysis(db: Session, user_id: int, job_id: int) -> SkillGapAnalysis:
    job = get_owned_job(db, user_id, job_id)
    user_skills = get_user_skills(db, user_id)

    if not user_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add at least one skill to your profile before running a gap analysis.",
        )
    if not job.requirements:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This job has no extracted requirements yet — analyze the job description first.",
        )

    engine_results, overall_score = run_gap_analysis(job, user_skills)

    analysis = SkillGapAnalysis(
        user_id=user_id,
        job_description_id=job.id,
        overall_alignment_score=overall_score,
        status=AnalysisStatus.completed,
    )
    db.add(analysis)
    db.flush()

    for engine_result in engine_results:
        explanation_text, explanation_source = generate_explanation(engine_result)

        db.add(SkillGapResult(
            analysis_id=analysis.id,
            job_requirement_id=engine_result.job_requirement.id,
            matched_user_skill_id=(
                engine_result.match.matched_user_skill.id
                if engine_result.match.matched_user_skill else None
            ),
            similarity_score=engine_result.match.similarity_score,
            classification=engine_result.match.classification,
            match_method=engine_result.match.match_method,
            priority=engine_result.priority,
            explanation=explanation_text,
            explanation_source=explanation_source,
        ))

    db.commit()
    db.refresh(analysis)
    return analysis


def get_analysis(db: Session, user_id: int, analysis_id: int) -> SkillGapAnalysis:
    return _get_owned_analysis(db, user_id, analysis_id)


def get_analysis_results(db: Session, user_id: int, analysis_id: int) -> list[SkillGapResult]:
    analysis = _get_owned_analysis(db, user_id, analysis_id)
    return analysis.results


def get_user_analyses(db: Session, user_id: int) -> list[SkillGapAnalysis]:
    return (
        db.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.user_id == user_id)
        .order_by(SkillGapAnalysis.created_at.desc())
        .all()
    )