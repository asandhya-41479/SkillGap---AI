"""Module 5 Step 4: Gemini writes the wording; the rule engine's plan stays the source of truth.

Gemini only ever receives the verified plan and returns text for items already in it. Anything it
returns is validated, and priority/weeks/hours/order are never read from it. Invalid or missing
items fall back to templates, so generation never fails because of Gemini.
"""
import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.models.roadmap import GenerationSource, LearningStyle
from app.schemas.roadmap import PracticalTask
from app.services.roadmap.plan_types import PlannedItem, RoadmapConstraints, RulePlan

logger = logging.getLogger(__name__)

MODELS = ("gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite")  # tried in order; each has its own capacity
MAX_ATTEMPTS = 2            # first call + one retry for whatever is still missing/invalid
TIMEOUT_MS = 30_000         # give up on a stalled Gemini call after 30 s and use the fallback
SDK_ATTEMPTS = 3            # per call: retries 429/5xx (e.g. 503 overload) with 2 s, 4 s backoff + jitter

_BANNED = re.compile(
    r"https?://|www\.|job[- ]?ready|guarantee|get hired|land a job|"
    r"coursera|udemy|udacity|edx|pluralsight|youtube|freecodecamp|w3schools|geeksforgeeks",
    re.I,
)


_INSTRUCTIONS = """You write learning content for a personalised skill-gap roadmap.
The skills, their order, priority, hours and weeks in INPUT_JSON are verified and FIXED. Do not add,
remove, rename, reorder or re-prioritise them. "facts" states why each skill is on the roadmap; stay
consistent with it and do not claim the learner knows or lacks anything beyond INPUT_JSON.

Return ONLY JSON: {"summary": "2-3 sentence overview", "items": [ONE object per input item]}
Each item object: {"skill_key": exact key from input, "reason": 1-2 sentences on why this skill matters
for the target role, "topics": 3-6 short topics, "practical_tasks": 1-3 objects
{"title", "description", "type": "exercise"|"mini_project"|"project_task"} doable within approx_hours,
"project_task": one suggested task on the learner's practice project, "milestone": one verifiable outcome}

Rules: if reduced_scope is true cover core topics only; match learning_style and learner_level;
no URLs, no named courses, books, websites or products; no promises about jobs or timelines.
Practice project (suggestions only, nothing is changed automatically): SkillGap AI, a FastAPI +
PostgreSQL + SQLAlchemy backend with JWT auth, a React + Vite + Tailwind frontend, and Gemini/embedding analysis.
"""


class ItemContent(BaseModel):
    skill_key: str
    reason: str = Field(min_length=10, max_length=400)
    topics: list[str] = Field(min_length=2, max_length=6)
    practical_tasks: list[PracticalTask] = Field(min_length=1, max_length=4)
    project_task: str = Field(min_length=5, max_length=300)
    milestone: str = Field(min_length=5, max_length=250)

    @field_validator("skill_key")
    @classmethod
    def _norm(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")

    def _clean(self):
        if any(not 2 <= len(t.strip()) <= 80 for t in self.topics):
            raise ValueError("bad topic")
        text = " ".join([self.reason, self.project_task, self.milestone, *self.topics,
                         *(f"{t.title} {t.description}" for t in self.practical_tasks)])
        if _BANNED.search(text):
            raise ValueError("unsupported claim or external reference")
        return self


@dataclass
class RoadmapContent:
    summary: str
    items: dict[str, ItemContent]  # skill_key -> content, for every scheduled item
    source: GenerationSource


def _template(i: PlannedItem) -> ItemContent:
    n = i.skill_name
    return ItemContent(
        skill_key=i.skill_key,
        reason=i.reason,
        topics=[f"Core concepts of {n}", f"Setting up and using {n} in a small project", f"Common mistakes and debugging in {n}"],
        practical_tasks=[PracticalTask(title=f"{n} basics exercise", description=f"Build a small working example that uses {n}.", type="exercise")],
        project_task=f"Apply {n} to one small feature in your practice project.",
        milestone=f"A working, tested example that uses {n}.",
    )


def _summary(plan: RulePlan, c: RoadmapConstraints, todo: list[PlannedItem]) -> str:
    if not todo:
        return plan.feasibility_note or "No skills could be scheduled in the available time."

    s = (f"{len(todo)} skills planned for {plan.target_role} over {c.duration_weeks} weeks "
         f"(about {plan.scheduled_hours:g} of {plan.capacity_hours:g} available hours), starting with {todo[0].skill_name}.")
    if plan.deferred_items:
        s += f" {len(plan.deferred_items)} did not fit and are listed as deferred."
    return s


def _prompt(plan: RulePlan, c: RoadmapConstraints, style: LearningStyle, items: list[PlannedItem]) -> str:
    """Only verified plan data goes to Gemini: no name, email or user id."""
    payload = {
        "target_role": plan.target_role,
        "learner_level": c.experience_level.value,
        "learning_style": style.value,
        "already_known": plan.already_known,
        "items": [{
            "skill_key": i.skill_key, "skill": i.skill_name, "priority": i.priority.value,
            "importance": i.importance.value if i.importance else "prerequisite",
            "gap_type": i.gap_classification.value if i.gap_classification else "supplementary",
            "approx_hours": i.estimated_hours, "weeks": f"{i.start_week}-{i.end_week}",
            "prerequisites": i.prerequisites, "reduced_scope": i.reduced_scope, "facts": i.reason,
        } for i in items],
    }
    return f"{_INSTRUCTIONS}\nINPUT_JSON:\n{json.dumps(payload, indent=1)}"


def _parse(raw: str, allowed: set[str]) -> tuple[str | None, dict[str, ItemContent]]:
    """Valid items only. Unknown skills and duplicates are dropped; bad items are skipped."""
    data = json.loads(re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip())
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    s = data.get("summary")
    summary = s.strip() if isinstance(s, str) and 10 <= len(s.strip()) <= 500 and not _BANNED.search(s) else None

    out: dict[str, ItemContent] = {}
    for entry in data["items"] if isinstance(data.get("items"), list) else []:
        try:
            item = ItemContent.model_validate(entry)
        except ValidationError:
            continue
        if item.skill_key in allowed:
            out.setdefault(item.skill_key, item)
    return summary, out


@lru_cache(maxsize=1)
def _client():
    from google import genai
    from google.genai import types
    from app.core.config import settings
    return genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(
        timeout=TIMEOUT_MS, retry_options=types.HttpRetryOptions(attempts=SDK_ATTEMPTS, initial_delay=2, max_delay=10,
        http_status_codes=[500, 502, 503, 504])))

def _gemini_call(prompt: str) -> str:
    """Try each model in MODELS; the first that answers wins. Raises the last error if all fail."""
    from google.genai import types
    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3)
    for n, model in enumerate(MODELS):
        try:
            return _client().models.generate_content(model=model, contents=prompt, config=config).text
        except Exception:
            logger.warning("Gemini model %s failed", model, exc_info=True)
            if n == len(MODELS) - 1:
                raise



def generate_content(
    plan: RulePlan,
    constraints: RoadmapConstraints,
    style: LearningStyle = LearningStyle.balanced,
    call: Callable[[str], str] | None = None,
) -> RoadmapContent:
    """Never raises because of Gemini. Deferred items get no content (they are not on the schedule)."""
    call = call or _gemini_call
    todo = plan.scheduled_items
    ok: dict[str, ItemContent] = {}
    summary, pending = None, todo

    for _ in range(MAX_ATTEMPTS if todo else 0):
        try:
            s, got = _parse(call(_prompt(plan, constraints, style, pending)), {i.skill_key for i in pending})
        except Exception:
            logger.warning("Gemini roadmap generation failed", exc_info=True)
            continue
        summary = summary or s
        ok.update(got)
        pending = [i for i in todo if i.skill_key not in ok]
        if not pending:
            break

    if not todo or not ok:
        source = GenerationSource.rules_only
    elif len(ok) == len(todo):
        source = GenerationSource.gemini
    else:
        source = GenerationSource.partial_fallback
    return RoadmapContent(

        summary=summary or _summary(plan, constraints, todo),
        items={i.skill_key: ok.get(i.skill_key) or _template(i) for i in todo},
        source=source,
    )