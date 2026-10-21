"""Module 5 Step 8 tests: regenerate a roadmap as a new version (adapt keeps finished work, fresh restarts)."""
import json

from app.models.roadmap import RoadmapItem
from app.models.skill_gap import SkillGapAnalysis
from app.services.roadmap import roadmap_llm
from tests.test_roadmap_api import api, body, create  # noqa: F401  (api is a pytest fixture)
from tests.test_roadmap_llm import Fake, good_reply


def mark(api, rid, item, status):
    r = api.client.patch(f"/roadmaps/{rid}/items/{item['id']}", json={"status": status})
    assert r.status_code == 200
    return r.json()


def regen(api, rid, **kw):
    return api.client.post(f"/roadmaps/{rid}/regenerate", json=kw)


def by_name(detail):
    return {i["skill_name"]: i for i in detail["items"]}


def test_adapt_keeps_finished_work_replans_the_rest_and_supersedes_the_old_version(api):
    old = create(api)                                              # Docker, FastAPI scheduled; Kubernetes deferred
    docker, fastapi, _ = old["items"]
    done = mark(api, old["id"], docker, "completed")
    mark(api, old["id"], fastapi, "skipped")

    r = regen(api, old["id"], mode="adapt", hours_per_week=10)
    assert r.status_code == 201

    new = r.json()
    items = by_name(new)
    assert new["parent_roadmap_id"] == old["id"] and new["lifecycle"] == "active" and new["hours_per_week"] == 10
    assert [i["skill_name"] for i in new["items"]] == ["Docker", "FastAPI", "Kubernetes"]
    assert (items["Docker"]["status"], items["FastAPI"]["status"]) == ("completed", "skipped")
    assert items["Docker"]["completed_at"] == done["completed_at"] and items["Docker"]["start_week"] is None
    assert items["Docker"]["topics"] == by_name(old)["Docker"]["topics"]            # earlier study plan is kept
    assert items["Kubernetes"]["is_scheduled"] and items["Kubernetes"]["start_week"] == 1   # fits the new budget
    assert new["total_estimated_hours"] == items["Kubernetes"]["estimated_hours"]            # only what is left
    assert new["progress"]["completed_items"] == 1 and new["progress"]["skipped_items"] == 1
    assert new["source_analysis_changed"] is False

    before = api.client.get(f"/roadmaps/{old['id']}").json()                      # old version kept as history
    assert before["lifecycle"] == "superseded" and by_name(before)["Docker"]["status"] == "completed"
    assert [r["id"] for r in api.client.get("/roadmaps").json()] == [new["id"], old["id"]]


def test_in_progress_work_is_replanned_but_stays_in_progress(api):
    old = create(api)
    mark(api, old["id"], old["items"][0], "in_progress")
    new = regen(api, old["id"], mode="adapt").json()
    docker = by_name(new)["Docker"]
    assert docker["status"] == "in_progress" and docker["is_scheduled"] and docker["start_week"] == 1


def test_fresh_starts_over_and_ignores_progress(api):
    old = create(api)
    mark(api, old["id"], old["items"][0], "completed")
    new = regen(api, old["id"], mode="fresh").json()
    assert {i["status"] for i in new["items"]} == {"not_started"}
    assert [i["skill_name"] for i in new["items"]] == [i["skill_name"] for i in old["items"]]
    assert new["parent_roadmap_id"] == old["id"] and api.client.get(f"/roadmaps/{old['id']}").json()["lifecycle"] == "superseded"



def test_finished_skills_are_not_planned_or_sent_to_gemini_again(api, monkeypatch):
    old = create(api)
    for item in old["items"][:2]:
        mark(api, old["id"], item, "completed")
    fake = Fake(good_reply)
    monkeypatch.setattr(roadmap_llm, "_gemini_call", fake)
    new = regen(api, old["id"], mode="adapt", hours_per_week=10).json()
    assert by_name(new)["Kubernetes"]["is_scheduled"] and len(fake.prompts) == 1
    sent = json.loads(fake.prompts[0].split("INPUT_JSON:")[1])
    assert [i["skill"] for i in sent["items"]] == ["Kubernetes"]                   # only what is left
    assert "Docker" in sent["already_known"]                                       # finished work counts as known


def test_everything_finished_leaves_nothing_to_schedule(api, monkeypatch):
    old = create(api)
    for item in old["items"][:2]:
        mark(api, old["id"], item, "completed")
    new = regen(api, old["id"], mode="adapt", hours_per_week=10).json()
    kube = by_name(new)["Kubernetes"]
    fake = Fake(good_reply)
    monkeypatch.setattr(roadmap_llm, "_gemini_call", fake)
    mark(api, new["id"], kube, "skipped")
    last = regen(api, new["id"], mode="adapt").json()
    assert fake.prompts == [] and last["feasibility_note"].startswith("Everything from your previous roadmap")
    assert {i["status"] for i in last["items"]} == {"completed", "skipped"} and last["total_estimated_hours"] == 0
    assert last["progress"]["percent_complete"] == 100.0


def test_regenerate_works_when_gemini_is_down(api, monkeypatch):
    old = create(api)

    monkeypatch.setattr(roadmap_llm, "_gemini_call", Fake(RuntimeError("503")))
    new = regen(api, old["id"], mode="fresh").json()
    assert new["generation_source"] == "rules_only"
    assert all(i["topics"] for i in new["items"] if i["is_scheduled"])


def test_only_the_active_version_can_be_changed(api):
    old = create(api)
    new = regen(api, old["id"]).json()
    assert regen(api, old["id"]).status_code == 409
    assert api.client.patch(f"/roadmaps/{old['id']}/items/{old['items'][0]['id']}", json={"status": "completed"}).status_code == 409
    assert regen(api, new["id"]).status_code == 201                                  # the newest one still can


def test_regenerate_checks_ownership_and_input(api):
    old = create(api)
    assert regen(api, 9999).status_code == 404
    for bad in ({"mode": "wipe"}, {"hours_per_week": 0}, {"duration_weeks": 27}):
        assert regen(api, old["id"], **bad).status_code == 422
    api.as_user(api.other)
    assert regen(api, old["id"]).status_code == 404
    api.as_user(api.uid)
    assert api.client.get(f"/roadmaps/{old['id']}").json()["lifecycle"] == "active"   # nothing changed


def test_deleted_analysis_cannot_be_regenerated(api):
    old = create(api)
    with api.Session() as s:
        s.delete(s.get(SkillGapAnalysis, api.aid))
        s.commit()
    r = regen(api, old["id"])
    assert r.status_code == 400 and "deleted" in r.json()["detail"]

    with api.Session() as s:
        assert s.query(RoadmapItem).count() == 3                                       # nothing half-saved