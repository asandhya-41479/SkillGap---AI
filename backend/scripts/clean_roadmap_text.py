"""One-off clean-up for roadmaps saved BEFORE the language guard: removes non-English characters
(e.g. a stray "摘要") from stored Gemini text. Only touches text that contains such characters.
Run from the backend folder:  python -m scripts.clean_roadmap_text
"""
import re

from app.db.database import SessionLocal
from app.models.roadmap import Roadmap, RoadmapItem

BAD = re.compile(r"[^\t\n\r\x20-\x7E‘’“”–—…]+")


def clean(text):
    if not isinstance(text, str) or not BAD.search(text):
        return text, False
    return re.sub(r"\s{2,}", " ", BAD.sub(" ", text)).strip(), True


db = SessionLocal()
changed = 0
for rm in db.query(Roadmap).all():
    rm.summary, c = clean(rm.summary); changed += c
    rm.feasibility_note, c = clean(rm.feasibility_note); changed += c
for it in db.query(RoadmapItem).all():
    for field in ("reason", "project_task", "milestone"):
        new, c = clean(getattr(it, field))
        if c:
            setattr(it, field, new); changed += 1
    topics = [clean(t)[0] for t in (it.topics or [])]
    if topics != (it.topics or []):
        it.topics = topics; changed += 1
    tasks = [{**t, "title": clean(t.get("title"))[0], "description": clean(t.get("description"))[0]}
             for t in (it.practical_tasks or [])]
    if tasks != (it.practical_tasks or []):
        it.practical_tasks = tasks; changed += 1
db.commit()
db.close()
print(f"Cleaned {changed} text field(s).")
