from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.skill_gap import SkillGapAnalysisDetailResponse, SkillGapAnalysisResponse
from app.services import skill_gap_service

router = APIRouter(prefix="/gap-analysis", tags=["skill-gap"])


@router.post("/{job_id}", response_model=SkillGapAnalysisDetailResponse)
def run_gap_analysis(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = skill_gap_service.run_and_store_analysis(db, current_user.id, job_id)
    return SkillGapAnalysisDetailResponse(
        **SkillGapAnalysisResponse.model_validate(analysis).model_dump(),
        results=analysis.results,
    )


@router.get("", response_model=list[SkillGapAnalysisResponse])
def list_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return skill_gap_service.get_user_analyses(db, current_user.id)



@router.get("/{analysis_id}", response_model=SkillGapAnalysisResponse)
def get_analysis_summary(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return skill_gap_service.get_analysis(db, current_user.id, analysis_id)


@router.get("/{analysis_id}/results", response_model=list[SkillGapAnalysisDetailResponse.__fields__["results"].annotation])
def get_analysis_results(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return skill_gap_service.get_analysis_results(db, current_user.id, analysis_id)