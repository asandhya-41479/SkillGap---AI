"""Module 5 Step 5: verified gaps -> rule plan -> Gemini wording -> saved roadmap, in one transaction."""
from sqlalchemy.orm import Session

from app.models.roadmap import Roadmap, RoadmapItem
from app.schemas.roadmap import RoadmapCreate
from app.services.roadmap.gap_reader import load_plan_input
from app.services.roadmap.plan_types import PlannedItem, RoadmapConstraints
from app.services.roadmap.planner import plan_roadmap
from app.services.roadmap.roadmap_llm import ItemContent, generate_content


def _item(i: PlannedItem, text: ItemContent | None) -> RoadmapItem:
    """Skeleton fields always come from the rule plan; Gemini/template text only fills the wording."""
    row = RoadmapItem(
        job_requirement_id=i.job_requirement_id, skill_name=i.skill_name,
        gap_classification=i.gap_classification, importance=i.importance, priority=i.priority,
        effort_size=i.effort_size, estimated_hours=i.estimated_hours, is_scheduled=i.is_scheduled,
        start_week=i.start_week, end_week=i.end_week, order_index=i.order_index,
        prerequisites=i.prerequisites, is_supplementary=i.is_supplementary, reduced_scope=i.reduced_scope,
        reason=i.reason, topics=[], practical_tasks=[],
    )
    if text:  # scheduled items only; deferred items keep just the plan's reason plus why they were deferred
        row.reason, row.topics, row.project_task, row.milestone = text.reason, text.topics, text.project_task, text.milestone
        row.practical_tasks = [t.model_dump() for t in text.practical_tasks]
    else:
        row.reason = f"{i.reason} {i.deferred_reason or ''}".strip()
    return row


def generate_and_store(db: Session, user_id: int, data: RoadmapCreate, call=None) -> Roadmap:
    """Raises 404/400 (HTTPException) for a missing, foreign or failed analysis. Gemini problems never raise."""
    plan_input = load_plan_input(db, user_id, data.analysis_id)
    constraints = RoadmapConstraints(data.hours_per_week, data.duration_weeks, data.experience_level)
    plan = plan_roadmap(plan_input, constraints)
    content = generate_content(plan, constraints, data.learning_style, call)

    roadmap = Roadmap(
        user_id=user_id, analysis_id=data.analysis_id, title=f"{plan.target_role} Roadmap",
        target_role=plan.target_role, hours_per_week=data.hours_per_week, duration_weeks=data.duration_weeks,
        experience_level=data.experience_level, learning_style=data.learning_style,
        summary=content.summary, feasibility_note=plan.feasibility_note,
        total_estimated_hours=plan.scheduled_hours, capacity_hours=plan.capacity_hours,
        generation_source=content.source,
        input_snapshot={  # what this roadmap was built from, so a later change to the analysis can be detected
            "gaps": [{"skill": g.skill_name, "classification": g.classification.value, "priority": g.priority.value}
                     for g in plan_input.gaps],
            "known_skills": plan_input.known_skills,
        },
        items=[_item(i, content.items.get(i.skill_key)) for i in plan.items],
    )
    try:
        db.add(roadmap)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(roadmap)
    return roadmap