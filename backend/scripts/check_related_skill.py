"""Diagnose "related skills (X)" in a roadmap: is X in the profile now, and was it when the analysis ran?
Run from the backend folder:  python -m scripts.check_related_skill demo.skillgap@gmail.com
"""
import sys

from app.db.database import SessionLocal
from app.models.roadmap import Roadmap, RoadmapItem, RoadmapLifecycle
from app.models.skill import UserSkill
from app.models.skill_gap import SkillGapResult
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.email == sys.argv[1]).first() if len(sys.argv) > 1 else None
if user is None:
    sys.exit("Usage: python -m scripts.check_related_skill <email>  (no account with that email)")
print(f"Profile skills of {user.email}:", ", ".join(s.skill_name for s in db.query(UserSkill).filter_by(user_id=user.id)))
for rm in db.query(Roadmap).filter(Roadmap.user_id == user.id, Roadmap.lifecycle == RoadmapLifecycle.active):
    print(f"\nActive roadmap #{rm.id} ({rm.target_role}), from analysis #{rm.analysis_id}")
    for it in db.query(RoadmapItem).filter(RoadmapItem.roadmap_id == rm.id).order_by(RoadmapItem.order_index):
        if "related" not in (it.reason or "").lower():
            continue
        res = db.query(SkillGapResult).filter(SkillGapResult.analysis_id == rm.analysis_id,
                                              SkillGapResult.job_requirement_id == it.job_requirement_id).first()
        matched = res.matched_user_skill.skill_name if res and res.matched_user_skill else None
        print(f"  {it.skill_name}: \"{it.reason}\"")
        print(f"     Module 4 matched it to: {matched or 'a skill that has since been DELETED from the profile'}")
db.close()
