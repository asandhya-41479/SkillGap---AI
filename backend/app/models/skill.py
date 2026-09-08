import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class SkillCategory(str, enum.Enum):
    programming_language = "programming_language"
    framework = "framework"
    database = "database"
    ai_ml = "ai_ml"
    cloud = "cloud"
    devops = "devops"
    tool = "tool"
    other = "other"


class SkillLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"

    advanced = "advanced"


class EvidenceSource(str, enum.Enum):
    github = "github"


class DetectedVia(str, enum.Enum):
    language = "language"
    topic = "topic"


class UserSkill(Base):
    __tablename__ = "user_skills"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_name", name="uq_user_skill_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    skill_name = Column(String(100), nullable=False)  # normalized/canonical name
    category = Column(Enum(SkillCategory), nullable=False, default=SkillCategory.other)
    self_assessed_level = Column(Enum(SkillLevel), nullable=True)  # null if GitHub-only, no manual entry
    is_manual = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    evidence = relationship(
        "SkillEvidence", back_populates="user_skill", cascade="all, delete-orphan"

    )


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"

    id = Column(Integer, primary_key=True, index=True)
    user_skill_id = Column(
        Integer, ForeignKey("user_skills.id", ondelete="CASCADE"), nullable=False, index=True
    )

    source = Column(Enum(EvidenceSource), nullable=False, default=EvidenceSource.github)
    repo_name = Column(String(200), nullable=False)
    repo_url = Column(String(500), nullable=False)
    detected_via = Column(Enum(DetectedVia), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_skill = relationship("UserSkill", back_populates="evidence")