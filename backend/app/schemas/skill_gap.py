from datetime import datetime

from pydantic import BaseModel

from app.models.skill_gap import (
    AnalysisStatus,
    ExplanationSource,
    MatchClassification,
    MatchMethod,
    PriorityLevel,
)


class SkillGapResultResponse(BaseModel):
    id: int
    job_requirement_id: int
    matched_user_skill_id: int | None
    similarity_score: float | None
    classification: MatchClassification
    match_method: MatchMethod
    priority: PriorityLevel
    explanation: str | None
    explanation_source: ExplanationSource | None

    model_config = {"from_attributes": True}


class SkillGapAnalysisResponse(BaseModel):
    id: int
    job_description_id: int
    overall_alignment_score: float | None
    status: AnalysisStatus

    created_at: datetime

    model_config = {"from_attributes": True}


class SkillGapAnalysisDetailResponse(SkillGapAnalysisResponse):
    results: list[SkillGapResultResponse]