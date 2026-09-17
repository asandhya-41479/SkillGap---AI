from datetime import datetime

from pydantic import BaseModel, Field

from app.models.job import Importance, JobStatus, RequirementCategory


class JobCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    target_role: str = Field(min_length=1, max_length=100)
    raw_description: str = Field(min_length=50, max_length=10000)


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