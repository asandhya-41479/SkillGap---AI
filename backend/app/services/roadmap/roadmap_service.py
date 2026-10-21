"""Module 5 Steps 5-8: build and store a roadmap from verified gaps; read it, track progress, delete it,
and regenerate it (keeping finished work) when the plan needs to change."""
from dataclasses import replace
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.roadmap import ItemStatus, Roadmap, RoadmapItem, RoadmapLifecycle
from app.schemas.roadmap import (
    RoadmapCreate, RoadmapDetailResponse, RoadmapProgress, RoadmapRegenerate, RoadmapSummaryResponse,
)
from app.services.roadmap.dependency_graph import skill_key
from app.services.roadmap.gap_reader import load_plan_input
from app.services.roadmap.plan_types import PlanInput, PlannedItem, RoadmapConstraints
from app.services.roadmap.planner import plan_roadmap
from app.services.roadmap.roadmap_llm import ItemContent, generate_content


# ---------------------------------------------------------------- create (Step 5) and regenerate (Step 8)

NOTE_ALL_DONE = "Everything from your previous roadmap is already completed or skipped, so nothing is left to schedule."
_FINISHED = (ItemStatus.completed, ItemStatus.skipped)
_KEPT_COLUMNS = (  # copied unchanged when finished work is carried into a new version
    "job_requirement_id", "skill_name", "gap_classification", "importance", "priority", "effort_size",
    "estimated_hours", "is_scheduled", "prerequisites", "is_supplementary", "reduced_scope", "reason", "topics",
    "practical_tasks", "project_task", "milestone", "status", "completed_at",
)


def _item(i: PlannedItem, text: ItemContent | None, offset: int = 0, doing: bool = False) -> RoadmapItem:
    """Skeleton fields always come from the rule plan; Gemini/template text only fills the wording."""

    row = RoadmapItem(
        job_requirement_id=i.job_requirement_id, skill_name=i.skill_name,
        gap_classification=i.gap_classification, importance=i.importance, priority=i.priority,
        effort_size=i.effort_size, estimated_hours=i.estimated_hours, is_scheduled=i.is_scheduled,
        start_week=i.start_week, end_week=i.end_week, order_index=i.order_index + offset,
        prerequisites=i.prerequisites, is_supplementary=i.is_supplementary, reduced_scope=i.reduced_scope,
        reason=i.reason, topics=[], practical_tasks=[],
        status=ItemStatus.in_progress if doing and i.is_scheduled else ItemStatus.not_started,
    )
    if text:  # scheduled items only; deferred items keep just the plan's reason plus why they were deferred
        row.reason, row.topics, row.project_task, row.milestone = text.reason, text.topics, text.project_task, text.milestone
        row.practical_tasks = [t.model_dump() for t in text.practical_tasks]
    else:
        row.reason = f"{i.reason} {i.deferred_reason or ''}".strip()
    return row


def _snapshot(p: PlanInput) -> dict:
    """What a roadmap was built from, so a later change to the analysis can be detected."""
    return {
        "gaps": [{"skill": g.skill_name, "classification": g.classification.value, "priority": g.priority.value}
                 for g in p.gaps],
        "known_skills": p.known_skills,
    }


def _create(db: Session, user_id: int, analysis_id: int, hours: int, weeks: int, level, style, call,
            old: Roadmap | None = None, mode: str = "fresh") -> Roadmap:
    plan_input = load_plan_input(db, user_id, analysis_id)
    adapt = old is not None and mode == "adapt"
    kept = [i for i in old.items if i.status in _FINISHED] if adapt else []
    done = {skill_key(i.skill_name) for i in kept}

    # Finished (or skipped) skills are not planned again, and count as known so their dependants stay valid.
    planning = replace(plan_input, gaps=[g for g in plan_input.gaps if skill_key(g.skill_name) not in done],
                       known_skills=plan_input.known_skills + [i.skill_name for i in kept])
    constraints = RoadmapConstraints(hours, weeks, level)
    plan = plan_roadmap(planning, constraints)
    content = generate_content(plan, constraints, style, call)
    doing = {i.skill_name for i in old.items if i.status == ItemStatus.in_progress} if adapt else set()
    carried = [RoadmapItem(**{c: getattr(i, c) for c in _KEPT_COLUMNS}, order_index=n) for n, i in enumerate(kept)]

    roadmap = Roadmap(
        user_id=user_id, analysis_id=analysis_id, parent_roadmap_id=old.id if old else None,
        title=f"{plan.target_role} Roadmap", target_role=plan.target_role, hours_per_week=hours,
        duration_weeks=weeks, experience_level=level, learning_style=style, summary=content.summary,
        feasibility_note=NOTE_ALL_DONE if kept and not plan.items else plan.feasibility_note,
        total_estimated_hours=plan.scheduled_hours, capacity_hours=plan.capacity_hours,
        generation_source=content.source, input_snapshot=_snapshot(plan_input),
        items=carried + [_item(i, content.items.get(i.skill_key), len(kept), i.skill_name in doing) for i in plan.items],
    )
    if old:
        old.lifecycle = RoadmapLifecycle.superseded  # saved in the same commit as the new version
    try:
        db.add(roadmap)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(roadmap)
    return roadmap


def generate_and_store(db: Session, user_id: int, data: RoadmapCreate, call=None) -> Roadmap:
    """Raises 404/400 (HTTPException) for a missing, foreign or failed analysis. Gemini problems never raise."""

    return _create(db, user_id, data.analysis_id, data.hours_per_week, data.duration_weeks,
                   data.experience_level, data.learning_style, call)


def regenerate(db: Session, user_id: int, roadmap_id: int, data: RoadmapRegenerate, call=None) -> Roadmap:
    """New version of an active roadmap, built from the CURRENT Module 4 gaps. The old one is kept as history.
    'adapt' keeps completed/skipped work and in-progress status; 'fresh' starts everything again."""
    old = get_roadmap(db, user_id, roadmap_id)
    _require_active(old)
    if old.analysis_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "The gap analysis behind this roadmap was deleted, so it cannot be regenerated.")
    return _create(db, user_id, old.analysis_id, data.hours_per_week or old.hours_per_week,
                   data.duration_weeks or old.duration_weeks, old.experience_level, old.learning_style,
                   call, old, data.mode)


# ---------------------------------------------------------------- read / update / delete (Step 6)

def get_roadmap(db: Session, user_id: int, roadmap_id: int) -> Roadmap:
    """Someone else's roadmap looks exactly like a missing one (404)."""
    r = db.query(Roadmap).filter(Roadmap.id == roadmap_id, Roadmap.user_id == user_id).first()
    if r is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Roadmap not found")
    return r


def _require_active(r: Roadmap) -> None:
    if r.lifecycle != RoadmapLifecycle.active:
        raise HTTPException(status.HTTP_409_CONFLICT, "This roadmap was replaced by a newer version and is kept for history only.")



def list_roadmaps(db: Session, user_id: int) -> list[Roadmap]:
    return db.query(Roadmap).filter(Roadmap.user_id == user_id).order_by(Roadmap.created_at.desc(), Roadmap.id.desc()).all()


def progress(r: Roadmap) -> RoadmapProgress:
    """Roadmap progress only (self-reported task status). It says nothing about skill level or job readiness."""
    scheduled = [i for i in r.items if i.is_scheduled]
    count = lambda s: sum(i.status == s for i in scheduled)  # noqa: E731
    done, doing, skipped = count(ItemStatus.completed), count(ItemStatus.in_progress), count(ItemStatus.skipped)
    total = len(scheduled) - skipped
    return RoadmapProgress(
        total_items=total, completed_items=done, in_progress_items=doing, remaining_items=total - done - doing,
        skipped_items=skipped, deferred_items=len(r.items) - len(scheduled),
        percent_complete=round(done / total * 100, 1) if total else 0.0,
    )


def _source_changed(db: Session, r: Roadmap) -> bool:
    """True if the Module 4 analysis this roadmap came from was deleted or its gaps are no longer the same."""
    if r.analysis_id is None:
        return True
    try:
        now = _snapshot(load_plan_input(db, r.user_id, r.analysis_id))["gaps"]
    except HTTPException:
        return True
    key = lambda gaps: {(g["skill"], g["classification"], g["priority"]) for g in gaps}  # noqa: E731
    return key(now) != key((r.input_snapshot or {}).get("gaps", []))


def to_summary(r: Roadmap) -> RoadmapSummaryResponse:
    out = RoadmapSummaryResponse.model_validate(r)
    out.progress = progress(r)

    return out


def to_detail(db: Session, r: Roadmap) -> RoadmapDetailResponse:
    out = RoadmapDetailResponse.model_validate(r)
    out.progress, out.source_analysis_changed = progress(r), _source_changed(db, r)
    return out


def update_item_status(db: Session, user_id: int, roadmap_id: int, item_id: int, new: ItemStatus) -> RoadmapItem:
    roadmap = get_roadmap(db, user_id, roadmap_id)
    _require_active(roadmap)
    item = next((i for i in roadmap.items if i.id == item_id), None)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Roadmap item not found")
    if not item.is_scheduled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This skill did not fit the time budget, so it has no schedule to track yet.")
    item.status = new
    item.completed_at = (item.completed_at or datetime.utcnow()) if new == ItemStatus.completed else None
    db.commit()
    db.refresh(item)
    return item


def delete_roadmap(db: Session, user_id: int, roadmap_id: int) -> None:
    db.delete(get_roadmap(db, user_id, roadmap_id))  # items go with it; Module 4 data is untouched
    db.commit()