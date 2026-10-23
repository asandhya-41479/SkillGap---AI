"""Module 5 extras: re-ask Gemini for the wording of a roadmap that was built without it."""
import json

from app.services.roadmap import roadmap_llm
from tests.test_roadmap_adaptive import by_name, mark, regen  # noqa: F401
from tests.test_roadmap_api import api, create  # noqa: F401  (api is a pytest fixture)
from tests.test_roadmap_llm import Fake, entry, good_reply


def down(api, monkeypatch):
    monkeypatch.setattr(roadmap_llm, "_gemini_call", Fake(RuntimeError("503")))
    return create(api)


def improve(api, rid):
    return api.client.post(f"/roadmaps/{rid}/improve")


def skeleton(detail):
    return [(i["skill_name"], i["priority"], i["estimated_hours"], i["start_week"], i["end_week"], i["order_index"],
             i["status"], i["is_scheduled"], i["prerequisites"]) for i in detail["items"]]


def test_improve_replaces_only_the_wording_of_a_standard_wording_roadmap(api, monkeypatch):
    old = down(api, monkeypatch)
    assert old["generation_source"] == "rules_only"
    mark(api, old["id"], old["items"][0], "in_progress")                       # progress must survive
    old = api.client.get(f"/roadmaps/{old['id']}").json()
    monkeypatch.setattr(roadmap_llm, "_gemini_call", Fake(good_reply))

    r = improve(api, old["id"])
    assert r.status_code == 200
    new = r.json()
    assert new["generation_source"] == "gemini" and new["id"] == old["id"] and new["lifecycle"] == "active"
    assert new["summary"] == "A focused plan built around your gaps." and new["summary"] != old["summary"]
    assert by_name(new)["Docker"]["topics"] == ["Basics", "Core concepts", "Testing"]
    assert by_name(new)["Docker"]["topics"] != by_name(old)["Docker"]["topics"]
    assert skeleton(new) == skeleton(old)                                        # plan, hours and progress untouched
    assert by_name(new)["Kubernetes"]["topics"] == [] and not by_name(new)["Kubernetes"]["is_scheduled"]
    assert len(api.client.get("/roadmaps").json()) == 1                          # same roadmap, no new version


def test_improve_while_gemini_is_still_down_changes_nothing(api, monkeypatch):
    old = down(api, monkeypatch)
    r = improve(api, old["id"])
    assert r.status_code == 503 and "nothing was changed" in r.json()["detail"]
    assert api.client.get(f"/roadmaps/{old['id']}").json() == old


def test_partly_improved_roadmap_is_marked_partial_and_keeps_template_text_for_the_rest(api, monkeypatch):
    old = down(api, monkeypatch)
    only_first = lambda prompt: json.dumps({"summary": "A fine overall summary.", "items": [entry("docker")]})  # noqa: E731
    monkeypatch.setattr(roadmap_llm, "_gemini_call", Fake(only_first))
    new = improve(api, old["id"]).json()
    assert new["generation_source"] == "partial_fallback"
    assert by_name(new)["Docker"]["topics"] == ["Basics", "Core concepts", "Testing"]
    assert by_name(new)["FastAPI"]["topics"] == by_name(old)["FastAPI"]["topics"]    # still template
    assert new["summary"] == old["summary"]


def test_finished_tasks_are_left_alone_and_not_sent_to_gemini(api, monkeypatch):
    old = down(api, monkeypatch)
    done = mark(api, old["id"], old["items"][0], "completed")
    fake = Fake(good_reply)
    monkeypatch.setattr(roadmap_llm, "_gemini_call", fake)
    new = improve(api, old["id"]).json()
    sent = json.loads(fake.prompts[0].split("INPUT_JSON:")[1])
    assert [i["skill"] for i in sent["items"]] == ["FastAPI"]
    assert by_name(new)["Docker"]["topics"] == by_name(old)["Docker"]["topics"]
    assert by_name(new)["Docker"]["completed_at"] == done["completed_at"]
    assert by_name(new)["FastAPI"]["topics"] == ["Basics", "Core concepts", "Testing"]


def test_improve_is_refused_when_not_needed_or_not_allowed(api, monkeypatch):
    good = create(api)                                                           # built with working Gemini
    assert improve(api, good["id"]).status_code == 409
    old = down(api, monkeypatch)
    for item in old["items"][:2]:
        mark(api, old["id"], item, "skipped")
    assert improve(api, old["id"]).status_code == 400                           # no open tasks left
    newer = down(api, monkeypatch)
    regen(api, newer["id"])                                                      # newer["id"] is now an older version
    assert improve(api, newer["id"]).status_code == 409
    assert improve(api, 9999).status_code == 404
    api.as_user(api.other)
    assert improve(api, old["id"]).status_code == 404