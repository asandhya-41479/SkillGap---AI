from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.job import Importance
from app.models.roadmap import (
    EffortSize,
    GenerationSource,
    ItemStatus,
    LearningStyle,
    RoadmapLifecycle,
)
from app.models.skill import SkillLevel
from app.models.skill_gap import MatchClassification, PriorityLevel


# ---------- Requests ----------

class RoadmapCreate(BaseModel):
    analysis_id: int
    hours_per_week: int = Field(default=8, ge=1, le=40)
    duration_weeks: int = Field(default=8, ge=1, le=26)
    experience_level: SkillLevel = SkillLevel.intermediate
    learning_style: LearningStyle = LearningStyle.balanced


class RoadmapItemStatusUpdate(BaseModel):
    status: ItemStatus


class RoadmapRegenerate(BaseModel):
    """Step 8. 'adapt' keeps completed/skipped progress; 'fresh' rebuilds from scratch."""
    mode: Literal["adapt", "fresh"] = "adapt"
    hours_per_week: int | None = Field(default=None, ge=1, le=40)
    duration_weeks: int | None = Field(default=None, ge=1, le=26)


# ---------- Nested content ----------

class PracticalTask(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=600)
    type: Literal["exercise", "mini_project", "project_task"] = "exercise"


# ---------- Responses ----------

class RoadmapItemResponse(BaseModel):
    id: int
    job_requirement_id: int | None
    skill_name: str

    gap_classification: MatchClassification | None
    importance: Importance | None
    priority: PriorityLevel

    effort_size: EffortSize
    estimated_hours: float  # approximate — the UI must label it "≈"
    is_scheduled: bool
    start_week: int | None
    end_week: int | None
    order_index: int
    prerequisites: list[str]
    is_supplementary: bool
    reduced_scope: bool

    reason: str | None
    topics: list[str]
    practical_tasks: list[PracticalTask]
    project_task: str | None
    milestone: str | None

    status: ItemStatus
    completed_at: datetime | None

    model_config = {"from_attributes": True}

    @field_validator("prerequisites", "topics", mode="before")
    @classmethod
    def _none_to_empty_list(cls, v):
        return [] if v is None else v

    @field_validator("practical_tasks", mode="before")
    @classmethod
    def _none_to_empty_tasks(cls, v):
        return [] if v is None else v


class RoadmapProgress(BaseModel):
    """Roadmap progress ONLY. This is not skill proficiency or job readiness."""
    total_items: int          # scheduled items, excluding skipped
    completed_items: int
    in_progress_items: int
    remaining_items: int
    skipped_items: int
    deferred_items: int       # did not fit the time budget
    percent_complete: float   # completed / total_items * 100, rounded to 1 decimal


class RoadmapSummaryResponse(BaseModel):
    id: int
    analysis_id: int | None
    parent_roadmap_id: int | None
    title: str
    target_role: str
    hours_per_week: int
    duration_weeks: int
    experience_level: SkillLevel
    learning_style: LearningStyle
    generation_source: GenerationSource
    lifecycle: RoadmapLifecycle
    total_estimated_hours: float
    capacity_hours: float
    created_at: datetime
    progress: RoadmapProgress | None = None  # filled by the service on read

    model_config = {"from_attributes": True}


class RoadmapDetailResponse(RoadmapSummaryResponse):
    summary: str | None
    feasibility_note: str | None
    source_analysis_changed: bool = False  # filled by the service (Step 6)
    items: list[RoadmapItemResponse]