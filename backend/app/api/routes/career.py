from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.career import (
    ActionCategory,
    ActionStatus,
    ActionUpdateRequest,
    CareerActionOut,
    CareerPlanOut,
    InterviewPrepItemOut,
    InterviewPrepOut,
    InterviewPrepUpdateRequest,
    OpportunityMatchOut,
    OpportunityMatchRequest,
    OpportunitySourceStatus,
    PlanGenerateRequest,
)
from app.services.career import career_service as svc
from app.services.career import interview_service as prep
from app.services.career import opportunity_service as opp

router = APIRouter(prefix="/career", tags=["career"])


@router.get("/actions", response_model=list[CareerActionOut])
def list_actions(
    job_id: int | None = Query(default=None, ge=1),
    status: ActionStatus | None = Query(default=None),
    category: ActionCategory | None = Query(default=None),
    include_archived: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The current user's career actions (optionally for one target job)."""
    return svc.list_actions(db, user.id, job_id, status.value if status else None,
                            category.value if category else None, include_archived)


@router.patch("/actions/{action_id}", response_model=CareerActionOut)
def update_action(action_id: int, data: ActionUpdateRequest,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update status / evidence of one of YOUR actions. Another user's id returns 404."""
    return svc.update_action(db, user.id, action_id, data)


@router.get("/{analysis_id}/plan", response_model=CareerPlanOut)
def get_plan(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Stored career plan for this analysis' target job. stale=true means your progress changed since it was built."""
    plan, stale = svc.get_plan(db, user.id, analysis_id)
    return svc.plan_response(db, plan, stale)


@router.post("/{analysis_id}/plan/generate", response_model=CareerPlanOut)
def generate_plan(analysis_id: int, data: PlanGenerateRequest | None = None,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rebuild the plan if inputs changed (or force=true). Unchanged inputs return the cached plan."""
    plan, _ = svc.generate_plan(db, user.id, analysis_id, force=bool(data and data.force))
    return svc.plan_response(db, plan, False)


# ---------------------------------------------------------------- Step 6: interview preparation

@router.patch("/interview-prep/{item_id}", response_model=InterviewPrepItemOut)
def update_interview_item(item_id: int, data: InterviewPrepUpdateRequest,
                          user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark one of YOUR interview topics as PREPARED / NOT_STARTED. Another user's id returns 404."""
    return prep.update_item(db, user.id, item_id, data.status.value)


@router.get("/{analysis_id}/interview-prep", response_model=InterviewPrepOut)
def get_interview_prep(analysis_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Focused interview topics for this target job: gaps, role fundamentals and your own project."""
    items, stale, job_id = prep.get_prep(db, user.id, analysis_id)
    return prep.prep_response(db, user.id, job_id, items, stale)


@router.post("/{analysis_id}/interview-prep/generate", response_model=InterviewPrepOut)
def generate_interview_prep(analysis_id: int, data: PlanGenerateRequest | None = None,
                            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Refresh topics when priorities changed (force=true also regenerates questions)."""
    a = svc._owned_analysis(db, user.id, analysis_id)
    items, _ = prep.generate_prep(db, user.id, analysis_id, force=bool(data and data.force))
    return prep.prep_response(db, user.id, a.job_description_id, items, False)


# ---------------------------------------------------------------- Step 7: opportunity matching (real data only)

@router.get("/opportunities/source-status", response_model=OpportunitySourceStatus)
def opportunity_source_status(user: User = Depends(get_current_user)):
    """Which job-data sources exist. No external job API is configured, so no live listings are shown."""
    return opp.source_status()


@router.get("/opportunities/saved-jobs", response_model=list[OpportunityMatchOut])
def saved_job_opportunities(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Compare your profile with every job description you saved in Module 3 (highest coverage first)."""
    return opp.saved_job_matches(db, user.id)


@router.post("/opportunities/match", response_model=OpportunityMatchOut)
def match_opportunity(data: OpportunityMatchRequest, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Match a real job description you paste, or one of your saved jobs (job_id). Deterministic, no Gemini."""
    return opp.match(db, user.id, data)


@router.get("/opportunities", response_model=list[OpportunityMatchOut])
def opportunity_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Your saved comparisons of pasted job descriptions."""
    return opp.history(db, user.id)


@router.delete("/opportunities/{match_id}", status_code=204)
def delete_opportunity(match_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opp.delete(db, user.id, match_id)
