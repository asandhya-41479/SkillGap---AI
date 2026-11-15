"""One-off repair for roadmaps saved before the Module 5 fixes. Safe to run more than once.
  1. removes non-English characters (e.g. a stray "摘要") from stored Gemini text
  2. if an analysis has more than one ACTIVE roadmap, keeps the newest active and marks the others superseded
     (they stay viewable as older versions; nothing is deleted)
Run from the backend folder:  python -m scripts.repair_roadmaps
"""
import re

import app.main  # noqa: F401  (registers every model, exactly like the running app)
from app.db.database import SessionLocal
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapLifecycle

BAD = re.compile(r"[^\t\n\r\x20-\x7E‘’“”–—…]+")


def clean(text):
    if not isinstance(text, str) or not BAD.search(text):
        return text
    return re.sub(r"\s{2,}", " ", BAD.sub(" ", text)).strip()


db = SessionLocal()
fields = 0
for rm in db.query(Roadmap).all():
    for f in ("summary", "feasibility_note"):
        new = clean(getattr(rm, f))
        if new != getattr(rm, f):
            setattr(rm, f, new); fields += 1
for it in db.query(RoadmapItem).all():
    for f in ("reason", "project_task", "milestone"):
        new = clean(getattr(it, f))
        if new != getattr(it, f):
            setattr(it, f, new); fields += 1
    topics = [clean(t) for t in (it.topics or [])]
    if topics != (it.topics or []):
        it.topics = topics; fields += 1
    tasks = [{**t, "title": clean(t.get("title")), "description": clean(t.get("description"))}
             for t in (it.practical_tasks or [])]
    if tasks != (it.practical_tasks or []):
        it.practical_tasks = tasks; fields += 1

superseded = []
active = (db.query(Roadmap).filter(Roadmap.lifecycle == RoadmapLifecycle.active)
          .order_by(Roadmap.user_id, Roadmap.analysis_id, Roadmap.created_at.desc(), Roadmap.id.desc()).all())
seen = set()
for rm in active:
    key = (rm.user_id, rm.analysis_id)
    if key in seen:
        rm.lifecycle = RoadmapLifecycle.superseded
        superseded.append(rm.id)
    seen.add(key)
db.commit()
db.close()
print(f"Cleaned {fields} text field(s). Marked {len(superseded)} duplicate active roadmap(s) as superseded: {superseded or 'none'}")
