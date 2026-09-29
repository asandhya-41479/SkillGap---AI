import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.job import Importance
from app.models.skill import SkillLevel
from app.models.skill_gap import MatchClassification, PriorityLevel


class RoadmapLifecycle(str, enum.Enum):
    active = "active"
    superseded = "superseded"  # replaced by an adapted roadmap; kept for history


class GenerationSource(str, enum.Enum):
    gemini = "gemini"                        # all item content came from validated Gemini output

    partial_fallback = "partial_fallback"    # some items were repaired with deterministic templates
    rules_only = "rules_only"                # Gemini unavailable/invalid; fully template content


class LearningStyle(str, enum.Enum):
    balanced = "balanced"
    hands_on = "hands_on"
    theory_first = "theory_first"


class EffortSize(str, enum.Enum):
    small = "small"
    medium = "medium"
    large = "large"


class ItemStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class Roadmap(Base):
    __tablename__ = "roadmaps"
    __table_args__ = (
        CheckConstraint("hours_per_week BETWEEN 1 AND 40", name="ck_roadmap_hours_per_week"),
        CheckConstraint("duration_weeks BETWEEN 1 AND 26", name="ck_roadmap_duration_weeks"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)


    # Traceability to the Module 4 source of truth. SET NULL so deleting an analysis
    # does not destroy the user's roadmap (the input_snapshot preserves what it was built from).
    analysis_id = Column(
        Integer, ForeignKey("skill_gap_analyses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Set when this roadmap was produced by adapting an earlier one (Step 8).
    parent_roadmap_id = Column(
        Integer, ForeignKey("roadmaps.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title = Column(String(200), nullable=False)
    target_role = Column(String(150), nullable=False)  # copied from the job for display/history

    # User constraints
    hours_per_week = Column(Integer, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    experience_level = Column(Enum(SkillLevel), nullable=False, default=SkillLevel.intermediate)
    learning_style = Column(Enum(LearningStyle), nullable=False, default=LearningStyle.balanced)

    # Generated / computed content
    summary = Column(Text, nullable=True)
    feasibility_note = Column(Text, nullable=True)  # set when the time may be insufficient
    total_estimated_hours = Column(Float, nullable=False, default=0.0)  # scheduled items only
    capacity_hours = Column(Float, nullable=False, default=0.0)         # hours_per_week * duration_weeks

    generation_source = Column(
        Enum(GenerationSource), nullable=False, default=GenerationSource.rules_only
    )
    lifecycle = Column(Enum(RoadmapLifecycle), nullable=False, default=RoadmapLifecycle.active)

    # Verified gaps the roadmap was built from (used for traceability and staleness detection).

    input_snapshot = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    analysis = relationship("SkillGapAnalysis")
    items = relationship(
        "RoadmapItem",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapItem.order_index",
    )


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    __table_args__ = (
        UniqueConstraint("roadmap_id", "skill_name", name="uq_roadmap_skill_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)

    # Link back to the Module 4 requirement. NULL for supplementary (prerequisite) items
    # that are not part of the verified requirement set.
    job_requirement_id = Column(
        Integer, ForeignKey("job_requirements.id", ondelete="SET NULL"), nullable=True, index=True
    )

    skill_name = Column(String(100), nullable=False)  # canonical name, same form as Module 3/4


    # Verified facts copied from Module 4 (never produced by Gemini).
    gap_classification = Column(Enum(MatchClassification), nullable=True)  # NULL when supplementary
    importance = Column(Enum(Importance), nullable=True)                   # NULL when supplementary
    priority = Column(Enum(PriorityLevel), nullable=False)

    # Deterministic scheduling output (never produced by Gemini).
    effort_size = Column(Enum(EffortSize), nullable=False)
    estimated_hours = Column(Float, nullable=False)  # approximate
    is_scheduled = Column(Boolean, nullable=False, default=True)  # False = deferred (did not fit)
    start_week = Column(Integer, nullable=True)      # NULL when deferred
    end_week = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False)    # dependency-respecting learning order
    prerequisites = Column(JSON, nullable=False, default=list)  # list[str] of skill names
    is_supplementary = Column(Boolean, nullable=False, default=False)
    reduced_scope = Column(Boolean, nullable=False, default=False)

    # Content (Gemini-written, validated, or template fallback).
    reason = Column(Text, nullable=True)
    topics = Column(JSON, nullable=False, default=list)           # list[str]
    practical_tasks = Column(JSON, nullable=False, default=list)  # list[{title, description, type}]
    project_task = Column(Text, nullable=True)                    # recommendation only
    milestone = Column(Text, nullable=True)

    # User progress (self-reported).
    status = Column(Enum(ItemStatus), nullable=False, default=ItemStatus.not_started)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roadmap = relationship("Roadmap", back_populates="items")
    job_requirement = relationship("JobRequirement")