"""Plain data containers for the roadmap rule engine (no DB, no Gemini)."""
from dataclasses import dataclass, field

from app.models.job import Importance
from app.models.roadmap import EffortSize
from app.models.skill import SkillLevel
from app.models.skill_gap import MatchClassification, PriorityLevel


@dataclass(frozen=True)
class GapInput:
    """One verified Module 4 result that is an actual gap (classification != strong)."""
    job_requirement_id: int | None
    skill_name: str
    importance: Importance
    classification: MatchClassification
    priority: PriorityLevel               # Module 4's stored priority — never changed
    similarity_score: float | None = None
    matched_skill_name: str | None = None  # the user's closest skill, when Module 4 found one


@dataclass
class PlanInput:
    target_role: str
    gaps: list[GapInput]
    known_skills: list[str]  # user's profile skills + strongly matched requirements


@dataclass(frozen=True)
class RoadmapConstraints:
    hours_per_week: int
    duration_weeks: int

    experience_level: SkillLevel = SkillLevel.intermediate


@dataclass
class PlannedItem:
    skill_key: str
    skill_name: str
    job_requirement_id: int | None
    gap_classification: MatchClassification | None   # None for supplementary items
    importance: Importance | None                    # None for supplementary items
    priority: PriorityLevel
    effort_size: EffortSize
    estimated_hours: float                            # approximate
    is_scheduled: bool
    start_week: int | None
    end_week: int | None
    order_index: int
    prerequisites: list[str] = field(default_factory=list)            # in-plan skills to learn first
    satisfied_prerequisites: list[str] = field(default_factory=list)  # prerequisites already known
    prerequisite_for: list[str] = field(default_factory=list)         # in-plan skills that need this
    is_supplementary: bool = False
    reduced_scope: bool = False
    reason: str = ""
    deferred_reason: str | None = None


@dataclass
class RulePlan:
    target_role: str
    capacity_hours: float
    scheduled_hours: float
    items: list[PlannedItem]

    already_known: list[str]
    feasibility_note: str | None
    has_gaps: bool

    @property
    def scheduled_items(self) -> list[PlannedItem]:
        return [i for i in self.items if i.is_scheduled]

    @property
    def deferred_items(self) -> list[PlannedItem]:
        return [i for i in self.items if not i.is_scheduled]