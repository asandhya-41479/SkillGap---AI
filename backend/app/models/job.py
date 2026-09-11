import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class JobStatus(str, enum.Enum):
    pending = "pending"
    analyzed = "analyzed"
    failed = "failed"


class RequirementCategory(str, enum.Enum):
    programming_language = "programming_language"
    framework = "framework"
    library = "library"
    database = "database"
    ai_ml = "ai_ml"
    cloud = "cloud"
    devops = "devops"
    api = "api"
    tool = "tool"
    concept = "concept"
    other = "other"


class Importance(str, enum.Enum):
    required = "required"
    preferred = "preferred"

    optional = "optional"


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(200), nullable=True)
    target_role = Column(String(100), nullable=False)
    raw_description = Column(Text, nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.pending)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")


class JobRequirement(Base):
    __tablename__ = "job_requirements"
    __table_args__ = (UniqueConstraint("job_description_id", "skill_name", name="uq_job_skill_name"),)

    id = Column(Integer, primary_key=True, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)

    skill_name = Column(String(100), nullable=False)
    category = Column(Enum(RequirementCategory), nullable=False, default=RequirementCategory.other)
    importance = Column(Enum(Importance), nullable=False, default=Importance.optional)
    source = Column(String(50), nullable=False, default="gemini")
    confidence = Column(Float, nullable=True)


    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("JobDescription", back_populates="requirements")