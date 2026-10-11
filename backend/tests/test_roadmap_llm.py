"""Module 5 Step 4 tests: Gemini content layer, driven by fake Gemini responses (no key, no network)."""
import copy
import json
import re
import sys
from types import SimpleNamespace

import pytest

from app.models.job import Importance as I
from app.models.roadmap import GenerationSource as S
from app.models.skill import SkillLevel as L
from app.models.skill_gap import MatchClassification as C, PriorityLevel as P
from app.services.roadmap.plan_types import GapInput, PlanInput, RoadmapConstraints
from app.services.roadmap.planner import plan_roadmap
from app.services.roadmap import roadmap_llm
from app.services.roadmap.roadmap_llm import ItemContent, generate_content


def entry(key, **over):
    e = {"skill_key": key, "reason": f"Why {key} matters for this role.", "topics": ["Basics", "Core concepts", "Testing"],
         "practical_tasks": [{"title": "Exercise", "description": "Build a small example.", "type": "exercise"}],
         "project_task": f"Add a {key} feature to your practice project.", "milestone": f"A tested {key} example."}
    return {**e, **over}


def good_reply(prompt):
    keys = re.findall(r'"skill_key": "(.*?)"', prompt)
    return json.dumps({"summary": "A focused plan built around your gaps.", "items": [entry(k) for k in keys]})


def make_plan(gaps, known=("Python", "SQL"), hpw=10, weeks=8, level=L.intermediate):

    c = RoadmapConstraints(hpw, weeks, level)
    return plan_roadmap(PlanInput("AI Engineer", gaps, list(known)), c), c


def g(name, cls=C.gap, pri=P.high, imp=I.required):
    return GapInput(None, name, imp, cls, pri, 0.1, None)


GAPS = [g("FastAPI"), g("Docker"), g("RAG")]


class Fake:
    """Scripted Gemini: returns / raises each reply in turn and records prompts."""
    def __init__(self, *replies):
        self.replies, self.prompts = list(replies), []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        r = self.replies.pop(0) if self.replies else self.replies_last
        self.replies_last = r
        if isinstance(r, Exception):
            raise r
        return r(prompt) if callable(r) else r


def test_valid_output_is_used_and_plan_is_untouched():
    plan, c = make_plan(GAPS)
    before = copy.deepcopy(plan)
    out = generate_content(plan, c, call=Fake(good_reply))
    assert out.source == S.gemini and set(out.items) == {i.skill_key for i in plan.scheduled_items}
    assert plan == before                                    # skeleton is never mutated
    assert out.summary == "A focused plan built around your gaps."



def test_gemini_cannot_override_priority_weeks_hours_or_add_skills():
    plan, c = make_plan(GAPS)
    keys = [i.skill_key for i in plan.scheduled_items]
    sneaky = [entry(k, priority="low", start_week=99, estimated_hours=1, order_index=-5) for k in keys]
    sneaky.append(entry("kubernetes"))                        # invented skill
    sneaky.append(entry(keys[0], reason="A duplicate that must be ignored."))
    out = generate_content(plan, c, call=Fake(json.dumps({"summary": "A fine overall summary.", "items": sneaky})))
    assert out.source == S.gemini and set(out.items) == set(keys)
    assert "kubernetes" not in out.items
    assert out.items[keys[0]].reason.startswith("Why")        # first entry wins over duplicate
    assert not hasattr(out.items[keys[0]], "priority") and not hasattr(out.items[keys[0]], "start_week")


def test_key_casing_is_normalized():
    plan, c = make_plan([g("FastAPI")])
    reply = json.dumps({"summary": "A fine overall summary.", "items": [entry("  FASTAPI ")]})
    assert generate_content(plan, c, call=Fake(reply)).source == S.gemini


@pytest.mark.parametrize("bad", [
    {"reason": "Short"},                                      # too short
    {"topics": ["only one"]},                                 # too few topics
    {"milestone": None},                                      # wrong type
    {"project_task": "See https://example.com/tutorial for this."},
    {"reason": "This will make you job-ready quickly."},
    {"milestone": "Guaranteed to pass any interview."},
    {"practical_tasks": [{"title": "Watch", "description": "Watch a Udemy course.", "type": "exercise"}]},
    {"practical_tasks": [{"title": "T", "description": "D", "type": "essay"}]},
    {"practical_tasks": []},
])

def test_invalid_items_fall_back_to_template_after_one_retry(bad):
    plan, c = make_plan(GAPS)
    keys = [i.skill_key for i in plan.scheduled_items]
    reply = json.dumps({"summary": "A fine overall summary.",
                        "items": [entry(keys[0], **bad)] + [entry(k) for k in keys[1:]]})
    fake = Fake(reply)                                        # retry returns the same bad reply
    out = generate_content(plan, c, call=fake)
    assert out.source == S.partial_fallback and len(fake.prompts) == 2
    assert out.items[keys[0]].reason == plan.scheduled_items[0].reason   # deterministic template used
    assert keys[1] not in fake.prompts[1] and keys[0] in fake.prompts[1]  # retry asks only for the bad item


def test_retry_recovers_a_missing_item():
    plan, c = make_plan(GAPS)
    keys = [i.skill_key for i in plan.scheduled_items]
    first = json.dumps({"summary": "A fine overall summary.", "items": [entry(k) for k in keys[:-1]]})
    out = generate_content(plan, c, call=Fake(first, good_reply))
    assert out.source == S.gemini and set(out.items) == set(keys)


@pytest.mark.parametrize("replies", [
    ["not json at all", "{broken"],
    ['["a list, not an object"]', "null"],
    [RuntimeError("quota exceeded"), TimeoutError("timeout")],
    [json.dumps({"summary": "x", "items": "nope"}), json.dumps({})],
])
def test_bad_or_failing_gemini_falls_back_without_raising(replies):
    plan, c = make_plan(GAPS)
    fake = Fake(*replies)
    out = generate_content(plan, c, call=fake)
    assert out.source == S.rules_only and len(fake.prompts) == 2
    assert set(out.items) == {i.skill_key for i in plan.scheduled_items}

    assert all(isinstance(v, ItemContent) for v in out.items.values())
    assert "planned for AI Engineer" in out.summary


def test_transient_failure_then_success():
    plan, c = make_plan(GAPS)
    out = generate_content(plan, c, call=Fake(RuntimeError("503"), good_reply))
    assert out.source == S.gemini


def test_fenced_json_is_accepted():
    plan, c = make_plan([g("Docker")])
    fenced = lambda prompt: "```json\n" + good_reply(prompt) + "\n```"
    assert generate_content(plan, c, call=Fake(fenced)).source == S.gemini


def test_bad_summary_is_replaced_by_template_but_items_still_count():
    plan, c = make_plan([g("Docker")])
    reply = json.dumps({"summary": "You will be job-ready in 30 days!", "items": [entry("docker")]})
    out = generate_content(plan, c, call=Fake(reply))
    assert out.source == S.gemini and "job-ready" not in out.summary and "planned for AI Engineer" in out.summary


def test_nothing_scheduled_means_no_gemini_call():
    empty, c = make_plan([])
    tiny, c2 = make_plan([g("Docker", pri=P.medium)], hpw=1, weeks=1)      # nothing fits
    for plan, cons in [(empty, c), (tiny, c2)]:
        fake = Fake(good_reply)
        out = generate_content(plan, cons, call=fake)
        assert fake.prompts == [] and out.items == {} and out.source == S.rules_only and out.summary



def test_prompt_contains_only_verified_plan_data():
    plan, c = make_plan(GAPS + [g("PostgreSQL", pri=P.low, imp=I.optional)], hpw=4, weeks=2)
    fake = Fake(good_reply)
    generate_content(plan, c, call=fake)
    prompt = fake.prompts[0]
    payload = json.loads(prompt.split("INPUT_JSON:\n", 1)[1])
    assert set(payload) == {"target_role", "learner_level", "learning_style", "already_known", "items"}
    assert [i["skill_key"] for i in payload["items"]] == [i.skill_key for i in plan.scheduled_items]
    assert all(set(i) >= {"priority", "gap_type", "approx_hours", "weeks", "facts"} for i in payload["items"])
    assert "FIXED" in prompt and "email" not in prompt.lower()
    assert not any(i.skill_name in json.dumps(payload["items"]) for i in plan.deferred_items)   # deferred not sent


@pytest.mark.parametrize("gaps,known,hpw,weeks,level", [
    ([g("Python"), g("Git")], [], 6, 10, L.beginner),
    ([g("FastAPI", C.partial, P.medium), g("PostgreSQL", C.partial, P.medium), g("Docker"), g("RAG")], ["Python", "SQL", "Git"], 10, 8, L.intermediate),
    ([g("FastAPI"), g("Docker"), g("PostgreSQL"), g("RAG")], ["Python"], 4, 4, L.intermediate),
])
def test_profiles_end_to_end(gaps, known, hpw, weeks, level):
    plan, c = make_plan(gaps, known, hpw, weeks, level)
    out = generate_content(plan, c, call=Fake(good_reply))
    assert out.source == S.gemini
    assert set(out.items) == {i.skill_key for i in plan.scheduled_items}      # never covers deferred items
    down = generate_content(plan, c, call=Fake(RuntimeError("down")))
    assert down.source == S.rules_only and set(down.items) == set(out.items)  # same coverage without Gemini


def test_gemini_client_is_built_with_a_request_timeout(monkeypatch):
    fake_config = SimpleNamespace(settings=SimpleNamespace(gemini_api_key="test-key"))
    monkeypatch.setitem(sys.modules, "app.core.config", fake_config)
    roadmap_llm._client.cache_clear()
    try:

        client = roadmap_llm._client()
        assert client._api_client._http_options.timeout == roadmap_llm.TIMEOUT_MS == 30_000
        assert client._api_client._http_options.retry_options.attempts == roadmap_llm.SDK_ATTEMPTS == 3
    finally:
        roadmap_llm._client.cache_clear()