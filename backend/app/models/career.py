"""
Module 7 — AI Career Action & Opportunity Intelligence Engine: database models.

Only 4 new tables; everything else is REUSED from Modules 3-6 by foreign key:
  job_descriptions (target role), skill_gap_analyses / skill_gap_results (gaps),
  roadmap_items (learning progress), progress_evidence (evidence), readiness_snapshots (readiness).

- Plans and actions are scoped per (user, target job) like Module 6 readiness. The job id stays the same when the
  user re-runs the gap analysis, so action status survives re-analysis (closed loop).
- Project recommendations are BUILD/PROVE actions (no project table). Skill priorities, evidence gaps and
  projects are cached as JSON on the plan snapshot.
- Module 7 enums are stored as VARCHAR (native_enum=False): adding a value never needs ALTER TYPE.
- Completing an action never edits a skill level. Evidence goes through Module 6 (evidence_id), and Module 6
  recalculates readiness.
"""
import enum

from app.core.time import utcnow

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    false,
    text,
    true,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class ActionCategory(str, enum.Enum):
    LEARN = "LEARN"
    BUILD = "BUILD"
    PRACTICE = "PRACTICE"
    PROVE = "PROVE"
    PREPARE = "PREPARE"
    APPLY = "APPLY"


class ActionPriority(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ActionStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class CareerStatus(str, enum.Enum):
    BUILDING_FOUNDATION = "BUILDING_FOUNDATION"
    DEVELOPING = "DEVELOPING"
    NEAR_READY = "NEAR_READY"
    READY_TO_APPLY = "READY_TO_APPLY"


class PrepKind(str, enum.Enum):
    GAP = "GAP"
    ROLE = "ROLE"
    PROJECT = "PROJECT"


class PrepStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PREPARED = "PREPARED"


class OpportunitySource(str, enum.Enum):
    SAVED_JOB = "SAVED_JOB"
    USER_PROVIDED = "USER_PROVIDED"
    JOB_API = "JOB_API"


def _enum(e):
    return Enum(e, native_enum=False, length=30, validate_strings=True)


class CareerPlan(Base):
    """One generated plan = one snapshot, and the cache: same input_hash -> reuse, no recomputation."""
    __tablename__ = "career_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"),
                                nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("skill_gap_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id", ondelete="SET NULL"), nullable=True)
    readiness_snapshot_id = Column(Integer, ForeignKey("readiness_snapshots.id", ondelete="SET NULL"), nullable=True)

    input_hash = Column(String(64), nullable=False)
    target_role = Column(String(150), nullable=False)
    readiness_score = Column(Float, nullable=True)      # live Module 6 result at generation time
    readiness_label = Column(String(30), nullable=True)

    career_status = Column(_enum(CareerStatus), nullable=False)
    status_criteria = Column(JSON, nullable=False, default=list)
    next_status = Column(JSON, nullable=True)
    skill_priorities = Column(JSON, nullable=False, default=list)
    evidence_gaps = Column(JSON, nullable=False, default=list)      # filled in Step 5
    projects = Column(JSON, nullable=False, default=list)           # filled in Step 5

    gemini_used = Column(Boolean, nullable=False, default=False, server_default=false())
    engine_version = Column(String(20), nullable=False)
    generated_at = Column(DateTime, default=utcnow, nullable=False)

    actions = relationship("CareerAction", back_populates="plan")

    __table_args__ = (Index("ix_career_plans_user_job_generated", "user_id", "job_description_id", "generated_at"),)


class CareerAction(Base):
    """The tracked unit. action_key = "<skill key>:<CATEGORY>" (or "apply:<item>") is stable across regenerations,
    so the user's status is kept when the plan is rebuilt."""
    __tablename__ = "career_actions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"),
                                nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("career_plans.id", ondelete="SET NULL"), nullable=True, index=True)

    action_key = Column(String(160), nullable=False)
    category = Column(_enum(ActionCategory), nullable=False)
    priority = Column(_enum(ActionPriority), nullable=False)
    priority_score = Column(Float, nullable=False, default=0.0)
    rank = Column(Integer, nullable=False, default=0)

    skill_name = Column(String(100), nullable=True)     # NULL for APPLY checklist actions
    importance = Column(String(20), nullable=True)      # Module 3 value, copied for display
    job_requirement_id = Column(Integer, ForeignKey("job_requirements.id", ondelete="SET NULL"), nullable=True)
    gap_result_id = Column(Integer, ForeignKey("skill_gap_results.id", ondelete="SET NULL"), nullable=True)
    roadmap_item_id = Column(Integer, ForeignKey("roadmap_items.id", ondelete="SET NULL"), nullable=True)
    blueprint_id = Column(String(80), nullable=True)    # project actions (Step 5)

    title = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)               # deterministic WHY, always present
    reason_codes = Column(JSON, nullable=False, default=list)
    explanation = Column(Text, nullable=True)           # optional validated Gemini wording (Step 4)
    evidence_required = Column(JSON, nullable=False, default=list)

    status = Column(_enum(ActionStatus), nullable=False, default=ActionStatus.NOT_STARTED)
    evidence_url = Column(String(500), nullable=True)
    evidence_note = Column(String(300), nullable=True)
    evidence_id = Column(Integer, ForeignKey("progress_evidence.id", ondelete="SET NULL"), nullable=True)

    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    plan = relationship("CareerPlan", back_populates="actions")

    __table_args__ = (
        Index("ix_career_actions_user_job_active", "user_id", "job_description_id", "is_active"),
        # one ACTIVE action per (user, job, key); archived history may repeat
        Index("uq_career_actions_active_key", "user_id", "job_description_id", "action_key", unique=True,
              postgresql_where=text("is_active = true"), sqlite_where=text("is_active = 1")),
    )


class InterviewPrepItem(Base):
    __tablename__ = "interview_prep_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"),
                                nullable=False, index=True)

    kind = Column(_enum(PrepKind), nullable=False)
    topic_id = Column(String(80), nullable=False)
    topic = Column(String(200), nullable=False)
    skill_name = Column(String(100), nullable=True)
    fact_id = Column(String(80), nullable=True)
    priority = Column(_enum(ActionPriority), nullable=False)
    why = Column(Text, nullable=False)
    questions = Column(JSON, nullable=False, default=list)

    status = Column(_enum(PrepStatus), nullable=False, default=PrepStatus.NOT_STARTED)
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    prepared_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (Index("ix_interview_prep_user_job_active", "user_id", "job_description_id", "is_active"),)


class OpportunityMatch(Base):
    """Created only for REAL data: a saved Module 3 job or a description the user pasted.
    Pasted text is not stored, only its hash and the extracted requirements."""
    __tablename__ = "opportunity_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(_enum(OpportunitySource), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True)
    source_url = Column(String(500), nullable=True)
    title = Column(String(200), nullable=True)      # only from the user/source, never generated
    company = Column(String(200), nullable=True)    # only from the user/source, never generated

    text_hash = Column(String(64), nullable=False)
    extracted_requirements = Column(JSON, nullable=False, default=list)
    coverage_pct = Column(Float, nullable=False)    # requirement coverage, NOT a hiring probability
    breakdown = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (Index("ix_opportunity_matches_user_created", "user_id", "created_at"),)
