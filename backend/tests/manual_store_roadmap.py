"""Manual end-to-end check on your real database + Gemini. From backend/ (venv active):
python -m tests.manual_store_roadmap <user_id> <analysis_id>"""
import sys

from app.db.database import SessionLocal
from app.models import github_connection, job, oauth_state, roadmap, skill, skill_gap, user  # noqa: F401
from app.schemas.roadmap import RoadmapCreate
from app.services.roadmap.roadmap_service import generate_and_store

user_id, analysis_id = map(int, sys.argv[1:3])
with SessionLocal() as db:
    r = generate_and_store(db, user_id, RoadmapCreate(analysis_id=analysis_id))
    print(f"roadmap {r.id}: {r.title} | source={r.generation_source.value} | {r.total_estimated_hours:g}/{r.capacity_hours:g} h")
    for i in r.items:
        when = f"weeks {i.start_week}-{i.end_week}" if i.is_scheduled else "DEFERRED"
        print(f"  {i.order_index}. {i.skill_name} [{i.priority.value}] ~{i.estimated_hours:g} h {when}")