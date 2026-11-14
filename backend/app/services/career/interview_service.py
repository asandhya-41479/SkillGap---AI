"""Module 7 Step 6: interview preparation persistence, caching and ownership.

- Topics are planned deterministically (interview_planner) from the SAME inputs as the career plan.
- Stable topic ids ("gap:docker", "role:dsa", "project:F_OWNERSHIP_404"): regeneration updates them in place and
  keeps the user's PREPARED status; topics no longer relevant are archived, never deleted.
- Gemini is called once, only for NEW GAP/ROLE topics (or all of them with force=True). Existing questions are
  kept, so opening the page never triggers a Gemini call.
- Marking HIGH topics as prepared changes Q, which changes the career plan's input hash (closed loop).
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.career import ActionPriority, InterviewPrepItem, PrepKind, PrepStatus
from app.schemas.career import InterviewPrepItemOut
from app.services.career import career_inputs, interview_questions
from app.services.career.action_engine import build_plan
from app.services.career.career_service import _owned_analysis
from app.services.career.interview_planner import plan_topics

INCLUDE_PROJECT_TOPICS = True     # project questions are about the SkillGap AI codebase itself


def _active(db: Session, user_id: int, job_id: int) -> list[InterviewPrepItem]:
    return (db.query(InterviewPrepItem)
            .filter(InterviewPrepItem.user_id == user_id, InterviewPrepItem.job_description_id == job_id,
                    InterviewPrepItem.is_active.is_(True))
            .order_by(InterviewPrepItem.id).all())


def _planned(db: Session, user_id: int, analysis_id: int):
    inputs = career_inputs.build(db, user_id, analysis_id)            # 404/400 like Module 6
    result = build_plan(inputs)                                       # deterministic, no Gemini
    return inputs, plan_topics(inputs, result.skill_priorities, INCLUDE_PROJECT_TOPICS)


def _signature(rows_or_specs) -> set:
    out = set()
    for x in rows_or_specs:
        if isinstance(x, dict):
            out.add((x["topic_id"], x["priority"], x["why"]))
        else:
            out.add((x.topic_id, x.priority.value if hasattr(x.priority, "value") else x.priority, x.why))
    return out


def generate_prep(db: Session, user_id: int, analysis_id: int, force: bool = False,
                  question_call=None) -> tuple[list[InterviewPrepItem], bool]:
    inputs, specs = _planned(db, user_id, analysis_id)
    job_id = inputs.job_description_id
    existing = {r.topic_id: r for r in _active(db, user_id, job_id)}
    if existing and not force and _signature(existing.values()) == _signature(specs):
        return list(existing.values()), False                        # unchanged: no writes, no Gemini

    new_specs = [s for s in specs if force or s["topic_id"] not in existing]
    gemini = interview_questions.generate(inputs.target_role, new_specs, call=question_call)   # before writes

    now = datetime.utcnow()
    wanted = set()
    for s in specs:
        wanted.add(s["topic_id"])
        row = existing.get(s["topic_id"])
        if row is None:
            row = InterviewPrepItem(user_id=user_id, job_description_id=job_id, topic_id=s["topic_id"],
                                    status=PrepStatus.NOT_STARTED)
            db.add(row)
        row.kind, row.topic, row.skill_name, row.fact_id = PrepKind(s["kind"]), s["topic"], s["skill_name"], s["fact_id"]
        row.priority, row.why, row.is_active = ActionPriority(s["priority"]), s["why"], True
        if s["topic_id"] in gemini:
            row.questions = gemini[s["topic_id"]]
        elif force or not row.questions or s["kind"] == "PROJECT":
            row.questions = s["questions"]                            # template / curated
        row.updated_at = now
    for tid, row in existing.items():
        if tid not in wanted:
            row.is_active = False                                     # archived, history kept
    db.commit()
    return _active(db, user_id, job_id), True


def get_prep(db: Session, user_id: int, analysis_id: int) -> tuple[list[InterviewPrepItem], bool, int]:
    """(items, stale, job_id). First visit generates; later visits only read (stale flag if priorities changed)."""
    a = _owned_analysis(db, user_id, analysis_id)
    items = _active(db, user_id, a.job_description_id)
    if not items:
        items, _ = generate_prep(db, user_id, analysis_id)
        return items, False, a.job_description_id
    _, specs = _planned(db, user_id, analysis_id)
    return items, _signature(items) != _signature(specs), a.job_description_id


def update_item(db: Session, user_id: int, item_id: int, status: str) -> InterviewPrepItem:
    row = db.query(InterviewPrepItem).filter(InterviewPrepItem.id == item_id,
                                             InterviewPrepItem.user_id == user_id).first()
    if row is None:
        raise HTTPException(404, "Interview topic not found")
    if not row.is_active:
        raise HTTPException(409, "This topic was replaced. Refresh your interview preparation.")
    row.status = PrepStatus(status)
    row.prepared_at = datetime.utcnow() if row.status == PrepStatus.PREPARED else None
    db.commit()
    db.refresh(row)
    return row


def prep_response(db: Session, user_id: int, job_id: int, items: list[InterviewPrepItem], stale: bool) -> dict:
    from app.models.job import JobDescription
    job = db.query(JobDescription).filter(JobDescription.id == job_id, JobDescription.user_id == user_id).first()
    high = [i for i in items if i.priority == ActionPriority.HIGH]
    prepared = sum(i.status == PrepStatus.PREPARED for i in high)
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    items = sorted(items, key=lambda i: (order[i.priority.value], {"GAP": 0, "PROJECT": 1, "ROLE": 2}[i.kind.value], i.id))
    return dict(
        job_description_id=job_id, target_role=(job.target_role if job else "Target role"), stale=stale,
        high_priority_total=len(high), high_priority_prepared=prepared,
        prepared_pct=round(100 * prepared / len(high), 1) if high else None,
        gemini_used=any(q.get("source") == "gemini" for i in items for q in (i.questions or [])),
        items=[InterviewPrepItemOut.model_validate(i) for i in items],
    )
