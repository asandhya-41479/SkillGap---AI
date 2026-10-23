from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.readiness import EvidenceKind, SnapshotTrigger, VerificationStatus


# ---------- Evidence ----------

class EvidenceCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)  # normalized by the service
    kind: EvidenceKind
    url: str = Field(min_length=12, max_length=500)
    note: str | None = Field(default=None, max_length=300)
    roadmap_item_id: int | None = None

    @field_validator("url")
    @classmethod
    def _https_only(cls, v: str) -> str:
        v = v.strip()
        if not v.lower().startswith("https://") or any(c.isspace() for c in v):
            raise ValueError("URL must start with https:// and contain no spaces")
        return v  # host / SSRF checks happen in the evidence service (Step 4)


class EvidenceResponse(BaseModel):
    id: int
    skill_name: str
    kind: EvidenceKind
    url: str
    repo_full_name: str | None

    verification_status: VerificationStatus
    verified_at: datetime | None
    note: str | None
    roadmap_item_id: int | None
    created_at: datetime
    strength: float | None = None  # filled by the service from kind + status; not stored

    model_config = {"from_attributes": True}


# ---------- Readiness ----------

class ReadinessComponents(BaseModel):
    """Each value is in [0, 1]. roadmap is None when no roadmap was used (weights were re-normalized)."""
    alignment: float | None
    required_coverage: float | None
    evidence: float | None
    gap_health: float | None
    roadmap: float | None


class ReadinessMetrics(BaseModel):
    """Counts kept on every snapshot so trends survive even if an old analysis is deleted."""
    alignment_pct: float | None = None   # Module 4's overall_alignment_score, unchanged
    strong: int = 0
    partial: int = 0
    transferable: int = 0
    gap: int = 0
    required_total: int = 0
    required_covered: int = 0            # required skills classified strong
    high_priority_open: int = 0          # Module 4 priority == high
    roadmap_pct: float | None = None



class NextAction(BaseModel):
    kind: Literal["roadmap_item", "add_evidence", "rerun_analysis"]
    title: str
    skill_name: str | None = None
    item_id: int | None = None
    reason_codes: list[str] = []
    alternatives: list[str] = []         # titles of the next-ranked candidates


class ReadinessSnapshotResponse(BaseModel):
    id: int
    job_description_id: int
    analysis_id: int | None
    roadmap_id: int | None
    score: float | None                  # None = "Not enough data"
    label: str | None
    components: ReadinessComponents
    metrics: ReadinessMetrics
    roadmap_included: bool
    formula_version: str
    trigger: SnapshotTrigger
    next_action: NextAction | None = None
    ai_feedback: str | None = None
    snapshot_date: date
    created_at: datetime


class ReadinessResponse(ReadinessSnapshotResponse):
    is_stale: bool = False               # inputs changed since this snapshot was computed



# ---------- History & comparison ----------

class HistoryPoint(BaseModel):
    snapshot_id: int
    analysis_id: int | None
    date: date
    score: float | None
    alignment_pct: float | None
    high_priority_open: int
    roadmap_pct: float | None


class ReadinessHistory(BaseModel):
    points: list[HistoryPoint]
    has_enough_history: bool             # needs >= 2 points; otherwise the UI shows "Not enough historical data."


class SkillChange(BaseModel):
    skill_name: str
    before: str                          # MatchClassification value
    after: str


class ReadinessComparison(BaseModel):
    """Before/after of two analyses. Alignment is in percentage points, never a relative %."""
    from_analysis_id: int
    to_analysis_id: int
    alignment_before: float | None
    alignment_after: float | None
    alignment_delta_points: float | None
    strong_before: int

    strong_after: int
    high_priority_before: int
    high_priority_after: int
    skill_changes: list[SkillChange]