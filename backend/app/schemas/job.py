from datetime import datetime

from pydantic import BaseModel, Field

from app.models.job import Importance, JobStatus, RequirementCategory

from pydantic import BaseModel, Field, field_validator


class JobCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    target_role: str = Field(min_length=1, max_length=100)
    raw_description: str = Field(min_length=50, max_length=10000)

    @field_validator("raw_description")
    @classmethod
    def description_must_have_real_content(cls, v: str) -> str:
        if len(v.strip()) < 50:
            raise ValueError("Job description must contain at least 50 non-whitespace characters.")
        return v


class JobRequirementResponse(BaseModel):
    skill_name: str
    category: RequirementCategory
    importance: Importance
    source: str
    confidence: float | None

    model_config = {"from_attributes": True}


class JobListItem(BaseModel):
    id: int
    title: str | None
    target_role: str
    status: JobStatus
    created_at: datetime

    model_config = {"from_attributes": True}



class JobDetail(JobListItem):
    raw_description: str
    updated_at: datetime
    requirements: list[JobRequirementResponse] = []