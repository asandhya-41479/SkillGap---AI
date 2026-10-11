"""Manual check against real Gemini. From backend/ with the venv active: python -m tests.manual_gemini_roadmap"""
from app.models.job import Importance as I
from app.models.skill import SkillLevel as L
from app.models.skill_gap import MatchClassification as C, PriorityLevel as P
from app.services.roadmap.plan_types import GapInput, PlanInput, RoadmapConstraints
from app.services.roadmap.planner import plan_roadmap
from app.services.roadmap.roadmap_llm import generate_content

gaps = [GapInput(None, "FastAPI", I.required, C.transferable, P.high, 0.5, "Flask"),
        GapInput(None, "Docker", I.required, C.gap, P.high),
        GapInput(None, "RAG", I.preferred, C.gap, P.medium)]
c = RoadmapConstraints(10, 8, L.intermediate)
plan = plan_roadmap(PlanInput("AI Engineer", gaps, ["Python", "SQL", "Flask"]), c)
out = generate_content(plan, c)
print("SOURCE:", out.source.value, "\nSUMMARY:", out.summary)
for key, item in out.items.items():
    print("\n" + key)
    print(item.model_dump_json(indent=1))