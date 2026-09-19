import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class AnalysisStatus(str, enum.Enum):
    completed = "completed"
    failed = "failed"


class MatchClassification(str, enum.Enum):
    strong = "strong"
    partial = "partial"
    transferable = "transferable"
    gap = "gap"


class MatchMethod(str, enum.Enum):
    exact = "exact"

    semantic = "semantic"
    none = "none"  # used for gap rows with no candidate at all


class PriorityLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"
    none = "none"  # strong matches — no action needed


class ExplanationSource(str, enum.Enum):
    gemini = "gemini"
    deterministic = "deterministic"


class SkillGapAnalysis(Base):
    __tablename__ = "skill_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    overall_alignment_score = Column(Float, nullable=True)  # null if status == failed
    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.completed)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    job = relationship("JobDescription")

    results = relationship(
        "SkillGapResult", back_populates="analysis", cascade="all, delete-orphan"
    )


class SkillGapResult(Base):
    __tablename__ = "skill_gap_results"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(
        Integer, ForeignKey("skill_gap_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_requirement_id = Column(
        Integer, ForeignKey("job_requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    matched_user_skill_id = Column(
        Integer, ForeignKey("user_skills.id", ondelete="SET NULL"), nullable=True, index=True
    )

    similarity_score = Column(Float, nullable=True)  # null when match_method == none
    classification = Column(Enum(MatchClassification), nullable=False)
    match_method = Column(Enum(MatchMethod), nullable=False, default=MatchMethod.none)
    priority = Column(Enum(PriorityLevel), nullable=False, default=PriorityLevel.none)

    explanation = Column(Text, nullable=True)
    explanation_source = Column(Enum(ExplanationSource), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    analysis = relationship("SkillGapAnalysis", back_populates="results")
    job_requirement = relationship("JobRequirement")
    matched_user_skill = relationship("UserSkill")