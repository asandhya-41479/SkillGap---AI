"""
Module 7 — Pydantic schemas (Pydantic v2).

1. Internal contract (Modules 4/5/6 -> Module 7): CareerInputs, built by services/career/career_inputs.py
2. Request bodies (validated user input; whitelisted fields only)
3. Response models

Values use the same lower-case strings as Modules 3-6 (required/preferred/optional,
strong/partial/transferable/gap, high/medium/low/none, not_started/in_progress/completed/skipped).
Module 7's own enums are UPPER-CASE so they are never confused with Module 4/5 values.
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ActionCategory(str, Enum):
    LEARN = "LEARN"; BUILD = "BUILD"; PRACTICE = "PRACTICE"
    PROVE = "PROVE"; PREPARE = "PREPARE"; APPLY = "APPLY"


class ActionPriority(str, Enum):
    HIGH = "HIGH"; MEDIUM = "MEDIUM"; LOW = "LOW"


class ActionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"; IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"; SKIPPED = "SKIPPED"


class CareerStatus(str, Enum):
    BUILDING_FOUNDATION = "BUILDING_FOUNDATION"; DEVELOPING = "DEVELOPING"
    NEAR_READY = "NEAR_READY"; READY_TO_APPLY = "READY_TO_APPLY"


class SkillState(str, Enum):
    NO_KNOWLEDGE = "NO_KNOWLEDGE"; TRANSFERABLE = "TRANSFERABLE"; PARTIAL = "PARTIAL"
    KNOWN_NO_EVIDENCE = "KNOWN_NO_EVIDENCE"; PROVEN = "PROVEN"


class PrepKind(str, Enum):
    GAP = "GAP"; ROLE = "ROLE"; PROJECT = "PROJECT"


class PrepStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"; PREPARED = "PREPARED"


class OpportunitySource(str, Enum):
    SAVED_JOB = "SAVED_JOB"            # a real job description the user saved in Module 3
    USER_PROVIDED = "USER_PROVIDED"    # a job description pasted for a one-off comparison
    JOB_API = "JOB_API"                # reserved: external job-data source (not configured)


Importance = Literal["required", "preferred", "optional"]
Classification = Literal["strong", "partial", "transferable", "gap"]
M4Priority = Literal["high", "medium", "low", "none"]
RoadmapStatus = Literal["not_started", "in_progress", "completed", "skipped"]


def _validate_https_url(v: Optional[str]) -> Optional[str]:
    if v is None or v.strip() == "":
        return None
    v = v.strip()
    p = urlparse(v)
    if p.scheme != "https" or not p.netloc:
        raise ValueError("URL must be a valid https:// link")
    return v


# ================================================================
# 1. INTERNAL CONTRACT
# ================================================================
class EvidenceRef(BaseModel):
    """One piece of evidence for display. Strength is computed by Module 6, never by Module 7."""
    source: Literal["progress_evidence", "github_detected", "roadmap"]
    kind: str = Field(..., max_length=50)            # project_url / github_repo / language / topic / completed_item
    url: Optional[str] = None
    status: Optional[str] = None                      # Module 6 verification_status when applicable
    strength: float = Field(..., ge=0, le=1)


class SkillInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)    # canonical name (Module 3/4 form)
    key: str = Field(..., min_length=1, max_length=100)     # skill_key(name), lower-case
    category: str = Field("other", max_length=40)           # Module 3 RequirementCategory value
    importance: Importance                                   # Module 3
    classification: Classification                          # Module 4
    m4_priority: M4Priority                                  # Module 4
    evidence_adjusted: bool = False                          # Module 6 raised gap -> partial via evidence
    gap_result_id: Optional[int] = None
    job_requirement_id: Optional[int] = None
    roadmap_item_id: Optional[int] = None                    # Module 5
    roadmap_status: Optional[RoadmapStatus] = None
    practical_done: bool = False
    prerequisites: List[str] = []                            # skill keys (Module 5 dependency graph)
    evidence_strength: float = Field(0.0, ge=0, le=1)        # Module 6 evidence_strengths
    evidence: List[EvidenceRef] = []


class ReadinessInput(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=100)       # None = Module 6 "Not enough data"
    label: Optional[str] = None
    snapshot_id: Optional[int] = None
    components: dict = {}


class CareerInputs(BaseModel):
    user_id: int
    analysis_id: int
    job_description_id: int
    target_role: str = Field(..., min_length=1, max_length=150)
    readiness: ReadinessInput
    roadmap_id: Optional[int] = None
    roadmap_pct: Optional[float] = Field(None, ge=0, le=100)     # None = no active roadmap
    interview_prep_pct: Optional[float] = Field(None, ge=0, le=100)  # None = not generated yet (Step 6)
    verifiable_skills: List[str] = []    # skill keys Module 6 can verify from repo files (github_evidence.SIGNALS)
    verification_hints: dict[str, str] = {}   # skill key -> the repository signal Module 6 looks for
    skills: List[SkillInput] = []
    fingerprint: str = ""                # Module 6 input fingerprint (part of the cache key)


# ================================================================
# 2. REQUEST BODIES
# ================================================================
class PlanGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    force: bool = False


class ActionUpdateRequest(BaseModel):
    """Users may change ONLY status + evidence. Priority, skill, score and category are system-owned."""
    model_config = ConfigDict(extra="forbid")

    status: Optional[ActionStatus] = None
    evidence_url: Optional[str] = Field(None, max_length=500)
    evidence_note: Optional[str] = Field(None, max_length=300)

    @field_validator("evidence_url")
    @classmethod
    def _check_evidence_url(cls, v):
        return _validate_https_url(v)

    @field_validator("evidence_note")
    @classmethod
    def _strip_note(cls, v):
        return (v.strip() or None) if v else None

    @model_validator(mode="after")
    def _not_empty(self):
        if self.status is None and self.evidence_url is None and self.evidence_note is None:
            raise ValueError("Provide at least one of: status, evidence_url, evidence_note")
        return self


class InterviewPrepUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: PrepStatus


class OpportunityMatchRequest(BaseModel):
    """A real job description pasted by the user, or one of the user's saved Module 3 jobs."""
    model_config = ConfigDict(extra="forbid")

    job_description: Optional[str] = Field(None, min_length=50, max_length=15000)
    job_id: Optional[int] = Field(None, ge=1)
    title: Optional[str] = Field(None, max_length=200)
    company: Optional[str] = Field(None, max_length=200)
    source_url: Optional[str] = Field(None, max_length=500)

    @field_validator("source_url")
    @classmethod
    def _check_source_url(cls, v):
        return _validate_https_url(v)

    @field_validator("title", "company")
    @classmethod
    def _strip(cls, v):
        return (v.strip() or None) if v else None

    @model_validator(mode="after")
    def _exactly_one_source(self):
        if bool(self.job_description) == bool(self.job_id):
            raise ValueError("Provide exactly one of job_description or job_id")
        return self


# ================================================================
# 3. RESPONSE MODELS
# ================================================================
class StatusCriterion(BaseModel):
    key: str
    label: str
    value: Optional[float]           # None = not available yet (shown as "not available")
    threshold: float
    comparator: Literal[">=", "<="]
    met: bool


class StatusTarget(BaseModel):
    """The next status up and which of its criteria are met. None when already READY_TO_APPLY."""
    status: CareerStatus
    met: int
    total: int
    criteria: List[StatusCriterion]


class SkillPriorityOut(BaseModel):
    skill_name: str
    importance: Importance
    classification: Classification
    state: SkillState
    category: ActionCategory
    priority: ActionPriority
    priority_score: float
    evidence_strength: float
    reason: str


class EvidenceGapOut(BaseModel):
    skill_name: str
    importance: Importance
    required_evidence: List[str]
    current_evidence: List[EvidenceRef]
    missing_evidence: List[str]
    recommended_action_key: Optional[str] = None
    recommended_action_title: Optional[str] = None


class ProjectRecommendationOut(BaseModel):
    blueprint_id: str
    name: str
    purpose: str
    skills_covered: List[str]            # skills this project PROVES (they had a BUILD gap)
    also_practises: List[str] = []       # other open skills of the role it exercises
    evidence_artifacts: List[str]
    description: Optional[str] = None
    action_key: Optional[str] = None


class CareerActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_key: str
    category: ActionCategory
    priority: ActionPriority
    priority_score: float
    rank: int
    skill_name: Optional[str]
    importance: Optional[str]
    gap_result_id: Optional[int]
    roadmap_item_id: Optional[int]
    blueprint_id: Optional[str]
    title: str
    reason: str
    reason_codes: List[str]
    explanation: Optional[str]
    evidence_required: List[str]
    status: ActionStatus
    evidence_url: Optional[str]
    evidence_note: Optional[str]
    evidence_id: Optional[int]
    is_active: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    updated_at: Optional[datetime]


class EvidenceResult(BaseModel):
    """What Module 6 did with the link of a completed action (Step 9 closed loop)."""
    evidence_id: Optional[int] = None
    skill_name: str
    kind: Optional[str] = None
    status: str                       # verified / linked / unverified / unavailable / rejected
    strength: Optional[float] = None  # Module 6 evidence strength
    detail: Optional[str] = None


class ActionUpdateOut(CareerActionOut):
    evidence_results: List[EvidenceResult] = []
    plan_stale: bool = False          # evidence changed: readiness and the plan are recalculated
    loop_message: Optional[str] = None


class CareerPlanOut(BaseModel):
    id: int
    analysis_id: Optional[int]
    job_description_id: int
    target_role: str
    readiness_score: Optional[float]
    readiness_label: Optional[str]
    career_status: CareerStatus
    status_criteria: List[StatusCriterion]
    next_status: Optional[StatusTarget]
    skill_priorities: List[SkillPriorityOut]
    evidence_gaps: List[EvidenceGapOut]
    projects: List[ProjectRecommendationOut]
    gemini_used: bool
    generated_at: datetime
    stale: bool = False
    next_milestone: Optional[CareerActionOut] = None
    top_actions: List[CareerActionOut] = []
    actions: List[CareerActionOut] = []
    disclaimer: str = ("Career status reflects how well your current skills and evidence match this target role. "
                       "It is not a guarantee of employment.")


class InterviewQuestion(BaseModel):
    question: str = Field(..., max_length=300)
    focus: Optional[str] = Field(None, max_length=200)
    answer_points: List[str] = []          # PROJECT questions: how SkillGap AI actually implements it (curated)
    source: Literal["gemini", "template", "curated"] = "template"


class InterviewPrepItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: PrepKind
    topic_id: str
    topic: str
    skill_name: Optional[str]
    fact_id: Optional[str]
    priority: ActionPriority
    why: str
    questions: List[InterviewQuestion]
    status: PrepStatus
    prepared_at: Optional[datetime]


class InterviewPrepOut(BaseModel):
    job_description_id: int
    target_role: str
    stale: bool = False                    # the role's priorities changed since these topics were built
    high_priority_total: int
    high_priority_prepared: int
    prepared_pct: Optional[float]          # Q in Career Status (HIGH topics prepared)
    gemini_used: bool
    items: List[InterviewPrepItemOut]
    note: str = ("Focused preparation from your target role's real gaps and your own project. "
                 "Project answers describe what SkillGap AI actually implements.")


class MatchBreakdown(BaseModel):
    strong: List[str] = []
    partial: List[str] = []
    transferable: List[str] = []
    missing: List[str] = []
    critical: List[str] = []                 # missing REQUIRED skills
    recommended_action_keys: List[str] = []  # your existing career actions that close these gaps


class OpportunityMatchOut(BaseModel):
    id: Optional[int] = None                 # None for saved jobs (computed live from Module 4, not stored)
    source: OpportunitySource
    job_description_id: Optional[int] = None
    analysis_id: Optional[int] = None
    source_url: Optional[str] = None
    title: Optional[str] = None              # only from the user / saved job, never generated
    company: Optional[str] = None            # only from the user, never generated
    target_role: Optional[str] = None
    needs_analysis: bool = False             # saved job without a completed Skill Gap Analysis
    coverage_pct: Optional[float] = None     # requirement coverage, NOT a hiring probability
    importance_detected: Optional[bool] = None
    extracted_requirements: List[dict] = []
    breakdown: MatchBreakdown = MatchBreakdown()
    created_at: Optional[datetime] = None
    summary: str = ""
    note: Optional[str] = None
    disclaimer: str = "This is a skill-requirement match, not a probability of being hired."


class OpportunitySourceStatus(BaseModel):
    saved_jobs_enabled: bool = True
    user_provided_enabled: bool = True
    job_api_configured: bool = False
    message: Optional[str] = "Live job listings require a connected job-data source. You can compare your saved job descriptions."
