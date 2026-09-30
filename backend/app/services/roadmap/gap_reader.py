"""Reads verified Module 4 results and turns them into rule-engine input.

Deliberately queries the models directly instead of importing skill_gap_service: that module
pulls in the embedding stack (sentence-transformers), which the roadmap engine does not need.
Ownership is enforced here: a missing or foreign analysis is a 404, same as Module 4.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.skill import UserSkill
from app.models.skill_gap import AnalysisStatus, MatchClassification, PriorityLevel, SkillGapAnalysis, SkillGapResult
from app.services.roadmap.plan_types import GapInput, PlanInput


def load_plan_input(db: Session, user_id: int, analysis_id: int) -> PlanInput:
    analysis = (
        db.query(SkillGapAnalysis)
        .options(
            joinedload(SkillGapAnalysis.job),
            joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement),
            joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.matched_user_skill),
        )
        .filter(SkillGapAnalysis.id == analysis_id, SkillGapAnalysis.user_id == user_id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    if analysis.status != AnalysisStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This gap analysis did not complete. Re-run it before generating a roadmap.",
        )

    user_skill_names = [
        s.skill_name for s in db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    ]

    gaps: list[GapInput] = []
    known: set[str] = set(user_skill_names)
    for r in analysis.results:
        req = r.job_requirement
        if req is None:
            continue
        if r.classification == MatchClassification.strong:
            known.add(req.skill_name)  # e.g. a semantic match: the requirement name counts as known
            continue
        if r.priority == PriorityLevel.none:
            continue
        gaps.append(GapInput(
            job_requirement_id=req.id,
            skill_name=req.skill_name,
            importance=req.importance,
            classification=r.classification,
            priority=r.priority,
            similarity_score=r.similarity_score,
            matched_skill_name=r.matched_user_skill.skill_name if r.matched_user_skill else None,
        ))

    return PlanInput(
        target_role=analysis.job.target_role,
        gaps=gaps,
        known_skills=sorted(known),
    )