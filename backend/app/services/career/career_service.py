"""Module 7 orchestration: inputs -> engine -> persist, with caching and ownership.

Caching: a plan is regenerated only when its input hash changes (Module 6 fingerprint covers gaps, evidence
strengths, roadmap statuses; plus Module 7 engine version and interview-prep progress). Opening the page
reads the stored plan; it never recomputes on every visit.

Stable actions: an action is identified by (user, job, action_key). Regeneration UPDATES the matching active
action (priority, rank, text) and keeps the user's status and evidence; actions no longer recommended are
archived (is_active = False), never deleted, so history is kept.
"""
import hashlib
import json
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import career_config as cfg
from app.models.career import ActionStatus, CareerAction, CareerPlan
from app.models.skill_gap import SkillGapAnalysis
from app.schemas.career import ActionUpdateRequest, CareerActionOut, CareerInputs
from app.services.career import career_explainer, career_inputs
from app.services.career.action_engine import EngineResult, build_plan

logger = logging.getLogger(__name__)

_UPDATABLE_FROM_ENGINE = ("category", "priority", "priority_score", "rank", "skill_name", "importance",
                          "job_requirement_id", "gap_result_id", "roadmap_item_id", "title", "reason",
                          "reason_codes", "evidence_required")
_BLUEPRINT = lambda c: c.action_key.split(":", 1)[1] if c.action_key.startswith("project:") else None  # noqa: E731


def input_hash(inputs: CareerInputs) -> str:
    raw = json.dumps([cfg.ENGINE_VERSION, inputs.fingerprint, inputs.analysis_id, inputs.target_role,
                      inputs.interview_prep_pct, inputs.readiness.score])
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------- ownership helpers

def _owned_analysis(db: Session, user_id: int, analysis_id: int) -> SkillGapAnalysis:
    a = db.query(SkillGapAnalysis).filter(SkillGapAnalysis.id == analysis_id,
                                          SkillGapAnalysis.user_id == user_id).first()
    if a is None:
        raise HTTPException(404, "Analysis not found")
    return a


def _owned_action(db: Session, user_id: int, action_id: int) -> CareerAction:
    act = db.query(CareerAction).filter(CareerAction.id == action_id, CareerAction.user_id == user_id).first()
    if act is None:                       # another user's id looks exactly like a missing id
        raise HTTPException(404, "Action not found")
    return act


def _latest_plan(db: Session, user_id: int, job_id: int) -> CareerPlan | None:
    return (db.query(CareerPlan).filter(CareerPlan.user_id == user_id, CareerPlan.job_description_id == job_id)
            .order_by(CareerPlan.generated_at.desc(), CareerPlan.id.desc()).first())


def _active_actions(db: Session, user_id: int, job_id: int) -> list[CareerAction]:
    return (db.query(CareerAction)
            .filter(CareerAction.user_id == user_id, CareerAction.job_description_id == job_id,
                    CareerAction.is_active.is_(True))
            .order_by(CareerAction.rank, CareerAction.id).all())


# ---------------------------------------------------------------- generate

def _explanations(db: Session, inputs: CareerInputs, result: EngineResult, call) -> dict[str, str]:
    """Reuse an accepted explanation when the action's deterministic text is unchanged; ask Gemini (one
    batched call) only for new/changed top actions. Returns action_key -> explanation."""
    old = {a.action_key: a for a in _active_actions(db, inputs.user_id, inputs.job_description_id)}
    top = result.actions[: cfg.EXPLAIN_MAX_ACTIONS]
    reused = {c.action_key: old[c.action_key].explanation for c in top
              if c.action_key in old and old[c.action_key].explanation
              and old[c.action_key].title == c.title and old[c.action_key].reason == c.reason}
    todo = [c for c in top if c.action_key not in reused]
    fresh = career_explainer.explain(inputs.target_role, result.status.status, todo, call=call).explanations
    return {**reused, **fresh}


def _persist(db: Session, inputs: CareerInputs, result: EngineResult, h: str,
             explanations: dict[str, str] | None = None) -> CareerPlan:
    explanations = explanations or {}
    st = result.status
    plan = CareerPlan(
        user_id=inputs.user_id, job_description_id=inputs.job_description_id, analysis_id=inputs.analysis_id,
        roadmap_id=inputs.roadmap_id, readiness_snapshot_id=inputs.readiness.snapshot_id, input_hash=h,
        target_role=inputs.target_role, readiness_score=inputs.readiness.score,
        readiness_label=inputs.readiness.label, career_status=st.status, status_criteria=st.criteria,
        next_status=st.next_status, skill_priorities=result.skill_priorities,
        evidence_gaps=result.evidence_gaps, projects=result.projects,
        gemini_used=bool(explanations), engine_version=cfg.ENGINE_VERSION,
    )
    db.add(plan)
    db.flush()

    existing = {a.action_key: a for a in _active_actions(db, inputs.user_id, inputs.job_description_id)}
    new_keys = set()
    for c in result.actions:
        new_keys.add(c.action_key)
        row = existing.get(c.action_key)
        if row is None:
            row = CareerAction(user_id=inputs.user_id, job_description_id=inputs.job_description_id,
                               action_key=c.action_key, status=ActionStatus.NOT_STARTED)
            db.add(row)
        for f in _UPDATABLE_FROM_ENGINE:
            setattr(row, f, getattr(c, f))
        row.blueprint_id = _BLUEPRINT(c)
        row.explanation = explanations.get(c.action_key)     # None -> UI shows the deterministic reason
        row.plan_id = plan.id
        row.is_active = True
    for key, row in existing.items():
        if key not in new_keys:
            row.is_active = False          # archived: no longer recommended, history kept
    return plan


def generate_plan(db: Session, user_id: int, analysis_id: int, force: bool = False,
                  explain_call=None) -> tuple[CareerPlan, bool]:
    """Returns (plan, generated). Reuses the latest plan when nothing relevant changed, unless force=True.
    explain_call replaces the Gemini call (tests); None uses the real Module 5 call chain."""
    inputs = career_inputs.build(db, user_id, analysis_id)      # 404/400 handled by Module 6 loader
    h = input_hash(inputs)
    latest = _latest_plan(db, user_id, inputs.job_description_id)
    if latest is not None and latest.input_hash == h and not force:
        return latest, False

    result = build_plan(inputs)
    explanations = _explanations(db, inputs, result, explain_call)   # network call: before any write
    try:
        plan = _persist(db, inputs, result, h, explanations)
        db.commit()
    except IntegrityError:                 # a parallel request generated the same plan first
        db.rollback()
        logger.info("Career plan generated concurrently; returning the stored one")
        plan = _latest_plan(db, user_id, inputs.job_description_id)
        if plan is None:
            raise HTTPException(409, "Plan generation conflict, please retry")
        return plan, False
    db.refresh(plan)
    return plan, True


def get_plan(db: Session, user_id: int, analysis_id: int) -> tuple[CareerPlan, bool]:
    """Stored plan + stale flag. The first visit generates one (deterministic, no Gemini, fast)."""
    a = _owned_analysis(db, user_id, analysis_id)
    plan = _latest_plan(db, user_id, a.job_description_id)
    if plan is None:
        plan, _ = generate_plan(db, user_id, analysis_id)
        return plan, False
    current = input_hash(career_inputs.build(db, user_id, analysis_id))
    return plan, plan.input_hash != current or plan.analysis_id != analysis_id


def plan_response(db: Session, plan: CareerPlan, stale: bool) -> dict:
    actions = [CareerActionOut.model_validate(a) for a in _active_actions(db, plan.user_id, plan.job_description_id)]
    open_actions = [a for a in actions if a.status.value not in ("COMPLETED", "SKIPPED")]
    return dict(
        id=plan.id, analysis_id=plan.analysis_id, job_description_id=plan.job_description_id,
        target_role=plan.target_role, readiness_score=plan.readiness_score, readiness_label=plan.readiness_label,
        career_status=plan.career_status, status_criteria=plan.status_criteria, next_status=plan.next_status,
        skill_priorities=plan.skill_priorities, evidence_gaps=plan.evidence_gaps, projects=plan.projects,
        gemini_used=plan.gemini_used, generated_at=plan.generated_at, stale=stale,
        next_milestone=open_actions[0] if open_actions else None,
        top_actions=open_actions[: cfg.TOP_ACTIONS], actions=actions,
    )


# ---------------------------------------------------------------- actions

def list_actions(db: Session, user_id: int, job_id: int | None = None, status: str | None = None,
                 category: str | None = None, include_archived: bool = False) -> list[CareerAction]:
    q = db.query(CareerAction).filter(CareerAction.user_id == user_id)
    if job_id is not None:
        q = q.filter(CareerAction.job_description_id == job_id)
    if not include_archived:
        q = q.filter(CareerAction.is_active.is_(True))
    if status:
        q = q.filter(CareerAction.status == status)
    if category:
        q = q.filter(CareerAction.category == category)
    return q.order_by(CareerAction.job_description_id, CareerAction.rank, CareerAction.id).all()


def update_action(db: Session, user_id: int, action_id: int, data: ActionUpdateRequest) -> CareerAction:
    """Only status and evidence fields change. Completing an action never marks a skill as mastered:
    evidence is passed to Module 6, which recalculates readiness (closed loop, Step 9)."""
    act = _owned_action(db, user_id, action_id)
    if not act.is_active:
        raise HTTPException(409, "This action was replaced by a newer plan. Refresh your career plan.")

    now = datetime.utcnow()
    if data.status is not None:
        new = ActionStatus(data.status.value)
        if new == ActionStatus.IN_PROGRESS and act.started_at is None:
            act.started_at = now
        if new == ActionStatus.COMPLETED:
            act.completed_at = now
            act.started_at = act.started_at or now
        elif act.completed_at is not None:
            act.completed_at = None        # moved back from completed
        act.status = new
    if data.evidence_url is not None:
        act.evidence_url = data.evidence_url
    if data.evidence_note is not None:
        act.evidence_note = data.evidence_note
    db.commit()
    db.refresh(act)
    return act
