"""Module 7 Step 6: interview preparation planner. Pure and deterministic: decides WHICH topics to prepare.

Three kinds of topics:
  GAP      the role's most important skills (from the Career Action Engine priorities), curated sub-topics
  ROLE     role fundamentals matched from the target role (DSA, system design, behavioural, ...)
  PROJECT  questions about the user's own SkillGap AI build, ONLY from the architecture facts manifest
Priority comes from the engine (GAP), the role mapping (ROLE) or the requirement overlap (PROJECT).
Gemini may later phrase GAP/ROLE questions (validated); PROJECT questions and answer points are curated.
"""
from app.core import career_config as cfg
from app.schemas.career import CareerInputs
from app.services.career import interview_catalog as ic
from app.services.career.project_facts import PROJECT_FACTS

_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
_STATE_TEXT = {
    "NO_KNOWLEDGE": "it is a current gap", "TRANSFERABLE": "you have a related foundation but not the skill yet",
    "PARTIAL": "it is only partly matched", "KNOWN_NO_EVIDENCE": "you know it but have no solid evidence yet",
    "PROVEN": "you have already demonstrated it, so expect detailed follow-up questions",
}
_TEMPLATES = ["Can you explain {sub} in {skill}?", "How have you used {sub} in {skill}, or how would you?",
              "What are common mistakes with {sub} in {skill}?", "How would you explain {sub} in {skill} to a teammate?",
              "What trade-offs matter for {sub} in {skill}?"]


def template_questions(skill: str, subtopics: list[str]) -> list[dict]:
    return [dict(question=_TEMPLATES[i % len(_TEMPLATES)].format(sub=sub, skill=skill), focus=sub,
                 answer_points=[], source="template")
            for i, sub in enumerate(subtopics[: cfg.PREP_QUESTIONS_MAX])]


def gap_topics(inputs: CareerInputs, skill_priorities: list[dict]) -> list[dict]:
    by_name = {s.name: s for s in inputs.skills}
    chosen = [p for p in skill_priorities
              if p["importance"] in ("required", "preferred") and p["priority"] in ("HIGH", "MEDIUM")]
    chosen.sort(key=lambda p: (_RANK[p["priority"]], p["importance"] != "required", -p["priority_score"]))
    out = []
    for p in chosen[: cfg.PREP_MAX_GAP_SKILLS]:
        s = by_name[p["skill_name"]]
        subs = ic.topics_for(s.key, s.category)[: cfg.PREP_SUBTOPICS_PER_SKILL]
        out.append(dict(
            topic_id=f"gap:{s.key}", kind="GAP", topic=s.name, skill_name=s.name, fact_id=None,
            priority=p["priority"], subtopics=subs,
            why=(f"{s.name} is a {s.importance} skill for {inputs.target_role} and {_STATE_TEXT[p['state']]}. "
                 f"Interviewers commonly probe: {', '.join(subs[:3])}."),
            questions=template_questions(s.name, subs),
        ))
    return out


def role_topics(inputs: CareerInputs) -> list[dict]:
    out = []
    for topic_id, title, subs in ic.fundamentals_for(inputs.target_role):
        out.append(dict(
            topic_id=topic_id, kind="ROLE", topic=title, skill_name=None, fact_id=None,
            priority="LOW" if topic_id == "role:behavioral" else "MEDIUM", subtopics=subs,
            why=f"Commonly asked in {inputs.target_role} interviews, independent of specific tools.",
            questions=template_questions(title, subs),
        ))
    return out


def project_topics(inputs: CareerInputs) -> list[dict]:
    """Facts relevant to this role's requirements (required = 2, preferred = 1); core facts break ties."""
    weight = {"required": 2, "preferred": 1, "optional": 0.5}
    role = {s.key: weight[s.importance] for s in inputs.skills}
    scored = []
    for f in PROJECT_FACTS:
        overlap = [k for k in f["skills"] if k in role]
        score = sum(role[k] for k in overlap) + (0.5 if f["core"] else 0)
        if overlap or f["core"]:
            scored.append((score, f, overlap))
    scored.sort(key=lambda t: (-t[0], t[1]["id"]))
    out = []
    for score, f, overlap in scored[: cfg.PREP_MAX_PROJECT_FACTS]:
        required_overlap = any(role[k] == 2 for k in overlap)
        names = [s.name for s in inputs.skills if s.key in overlap]
        qs = [dict(question=f["question"], focus=f["title"], answer_points=list(f["answer_points"]), source="curated")]
        qs += [dict(question=q, focus=f["title"], answer_points=[], source="curated") for q in f["follow_ups"]]
        out.append(dict(
            topic_id=f"project:{f['id']}", kind="PROJECT", topic=f"{f['title']} ({f['module']})", skill_name=None,
            fact_id=f["id"], priority="HIGH" if required_overlap else "MEDIUM", subtopics=[],
            why=("Interviewers ask how your own project works. This is how SkillGap AI actually implements it"
                 + (f", and it shows {', '.join(names[:3])} from this role's requirements." if names else ".")),
            questions=qs,
        ))
    return out


def plan_topics(inputs: CareerInputs, skill_priorities: list[dict], include_project: bool = True) -> list[dict]:
    topics = gap_topics(inputs, skill_priorities) + role_topics(inputs)
    if include_project:
        topics += project_topics(inputs)
    topics.sort(key=lambda t: (_RANK[t["priority"]], {"GAP": 0, "PROJECT": 1, "ROLE": 2}[t["kind"]]))
    return topics
