from datetime import datetime

from pydantic import BaseModel, Field

from app.models.skill import DetectedVia, EvidenceSource, SkillCategory, SkillLevel


class SkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=100)
    category: SkillCategory
    self_assessed_level: SkillLevel


class SkillUpdate(BaseModel):
    category: SkillCategory | None = None
    self_assessed_level: SkillLevel | None = None


class EvidenceItem(BaseModel):
    repo_name: str
    repo_url: str
    detected_via: DetectedVia

    model_config = {"from_attributes": True}


class SkillResponse(BaseModel):
    id: int
    skill_name: str
    category: SkillCategory
    self_assessed_level: SkillLevel | None
    is_manual: bool

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SkillProfileItem(BaseModel):
    """Used by GET /profile/skills — the unified view (Step 6)."""
    skill_name: str
    category: SkillCategory
    self_assessed_level: SkillLevel | None
    demonstrated: bool
    evidence_count: int
    evidence: list[EvidenceItem]
    sources: list[str]  # e.g. ["manual", "github"]