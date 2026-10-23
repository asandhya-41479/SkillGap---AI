import enum
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app.db.base import Base


class EvidenceKind(str, enum.Enum):
    project_url = "project_url"
    github_repo = "github_repo"


class VerificationStatus(str, enum.Enum):
    verified = "verified"        # GitHub checked: owned by the connected account + a skill signal found
    linked = "linked"            # URL accepted, content NOT verified
    unverified = "unverified"    # a GitHub check ran but could not confirm the skill
    unavailable = "unavailable"  # GitHub could not be reached; retry later


class SnapshotTrigger(str, enum.Enum):
    progress = "progress"
    evidence = "evidence"
    reanalysis = "reanalysis"
    manual = "manual"


class ProgressEvidence(Base):
    """Evidence the user attached to a skill (project link or GitHub repo).

    Keyed by canonical skill_name (same form as Module 3/4/5) because the skills that matter most
    are gaps the user does not hold yet, so there is no UserSkill row to point at. Module 2's
    SkillEvidence (auto-detected GitHub repos) is untouched. "Learning evidence" (a completed
    roadmap item) is derived from RoadmapItem, never stored here. Strength is derived from
    kind + verification_status in the readiness engine, so it is not stored.
    """
    __tablename__ = "progress_evidence"
    __table_args__ = (UniqueConstraint("user_id", "skill_name", "url", name="uq_evidence_user_skill_url"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    roadmap_item_id = Column(Integer, ForeignKey("roadmap_items.id", ondelete="SET NULL"), nullable=True)

    kind = Column(Enum(EvidenceKind), nullable=False)
    url = Column(String(500), nullable=False)
    repo_full_name = Column(String(200), nullable=True)  # "owner/repo", github_repo only
    verification_status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.linked)
    verified_at = Column(DateTime, nullable=True)
    note = Column(String(300), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ReadinessSnapshot(Base):
    """One computed Career Readiness result. References the analysis/roadmap it came from instead of
    copying the skill profile; per-skill detail is read from that analysis' SkillGapResult rows.
    At most one row per (user, job, analysis, day): same-day recalculations update it in place."""
    __tablename__ = "readiness_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "job_description_id", "analysis_id", "snapshot_date", name="uq_snapshot_day"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(
        Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    analysis_id = Column(Integer, ForeignKey("skill_gap_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id", ondelete="SET NULL"), nullable=True)

    score = Column(Float, nullable=True)        # 0-100; NULL = not enough data
    label = Column(String(30), nullable=True)

    # Components, each in [0, 1] (see readiness_config for the formula). p is NULL when no roadmap.
    a_alignment = Column(Float, nullable=True)
    c_required_coverage = Column(Float, nullable=True)
    e_evidence = Column(Float, nullable=True)
    g_gap_health = Column(Float, nullable=True)
    p_roadmap = Column(Float, nullable=True)
    roadmap_included = Column(Boolean, nullable=False, default=True)

    metrics = Column(JSON, nullable=False, default=dict)  # counts/percentages for trends (schemas.readiness.ReadinessMetrics)
    next_action = Column(JSON, nullable=True)             # deterministic choice + reason codes
    ai_feedback = Column(Text, nullable=True)             # optional Gemini wording, cached

    formula_version = Column(String(20), nullable=False)
    input_fingerprint = Column(String(64), nullable=False)  # hash of inputs; detects a stale snapshot
    trigger = Column(Enum(SnapshotTrigger), nullable=False, default=SnapshotTrigger.manual)
    snapshot_date = Column(Date, nullable=False, default=date.today)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)