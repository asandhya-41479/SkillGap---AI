"""Module 5 Step 6 tests: roadmap HTTP API (real router, in-memory DB, fake login, fake Gemini)."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.roadmaps import router
from app.db.base import Base
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models import github_connection, job, oauth_state, roadmap, skill, skill_gap, user  # noqa: F401
from app.models.roadmap import RoadmapItem
from app.models.skill_gap import PriorityLevel as P, SkillGapAnalysis, SkillGapResult
from app.services.roadmap import roadmap_llm
from tests.test_roadmap_llm import Fake, good_reply
from tests.test_roadmap_rule_engine import seed


@pytest.fixture()
def api(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        u, other, a = seed(s)
        ids = (u.id, other.id, a.id)
    monkeypatch.setattr(roadmap_llm, "_gemini_call", Fake(good_reply))


    def session():
        with Session() as s:
            yield s

    app, who = FastAPI(), {"id": ids[0]}
    app.include_router(router)
    app.dependency_overrides[get_db] = session
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=who["id"])
    return SimpleNamespace(client=TestClient(app), app=app, Session=Session, uid=ids[0], other=ids[1], aid=ids[2],
                           as_user=lambda uid: who.update(id=uid))


def body(api, **kw):
    return {"analysis_id": api.aid, "hours_per_week": 6, "duration_weeks": 4, **kw}


def create(api):
    r = api.client.post("/roadmaps", json=body(api))
    assert r.status_code == 201
    return r.json()


def test_create_returns_detail_with_progress_and_is_listed(api):
    d = create(api)
    assert d["generation_source"] == "gemini" and d["source_analysis_changed"] is False
    assert [i["skill_name"] for i in d["items"]] == ["Docker", "FastAPI", "Kubernetes"]       # learning order
    assert d["progress"] == {"total_items": 2, "completed_items": 0, "in_progress_items": 0, "remaining_items": 2,
                             "skipped_items": 0, "deferred_items": 1, "percent_complete": 0.0}
    create(api)
    rows = api.client.get("/roadmaps").json()
    assert [r["id"] for r in rows] == [2, 1] and rows[0]["progress"]["total_items"] == 2   # newest first

    assert "items" not in rows[0]


def test_login_is_required(api):
    api.app.dependency_overrides.pop(get_current_user)
    for method, url, kw in [("GET", "/roadmaps", {}), ("POST", "/roadmaps", {"json": body(api)}),
                            ("GET", "/roadmaps/1", {}), ("GET", "/roadmaps/1/progress", {}),
                            ("PATCH", "/roadmaps/1/items/1", {"json": {"status": "completed"}}), ("DELETE", "/roadmaps/1", {})]:
        assert api.client.request(method, url, **kw).status_code in (401, 403), url


def test_other_users_cannot_see_change_or_delete_a_roadmap(api):
    d = create(api)
    rid, item = d["id"], d["items"][0]["id"]
    api.as_user(api.other)
    assert api.client.get("/roadmaps").json() == []
    for method, url, kw in [("GET", f"/roadmaps/{rid}", {}), ("GET", f"/roadmaps/{rid}/progress", {}),
                            ("PATCH", f"/roadmaps/{rid}/items/{item}", {"json": {"status": "completed"}}),
                            ("DELETE", f"/roadmaps/{rid}", {})]:
        assert api.client.request(method, url, **kw).status_code == 404, url
    assert api.client.post("/roadmaps", json=body(api)).status_code == 404         # someone else's analysis
    api.as_user(api.uid)
    assert api.client.get(f"/roadmaps/{rid}").json()["items"][0]["status"] == "not_started"   # untouched


@pytest.mark.parametrize("bad", [{"hours_per_week": 0}, {"hours_per_week": 41}, {"duration_weeks": 0},
                                 {"duration_weeks": 27}, {"experience_level": "wizard"}, {"learning_style": "x"}])
def test_invalid_constraints_are_rejected(api, bad):
    assert api.client.post("/roadmaps", json=body(api, **bad)).status_code == 422
    assert api.client.get("/roadmaps").json() == []



def test_unknown_analysis_and_missing_roadmap_are_404(api):
    assert api.client.post("/roadmaps", json=body(api, analysis_id=9999)).status_code == 404
    assert api.client.get("/roadmaps/9999").status_code == 404


def test_item_status_flow_sets_and_clears_completed_at(api):
    d = create(api)
    url = f"/roadmaps/{d['id']}/items/{d['items'][0]['id']}"
    patch = lambda s: api.client.patch(url, json={"status": s})  # noqa: E731
    assert patch("in_progress").json()["completed_at"] is None
    done = patch("completed").json()
    assert done["status"] == "completed" and done["completed_at"]
    assert patch("completed").json()["completed_at"] == done["completed_at"]       # not re-stamped
    back = patch("not_started").json()
    assert back["status"] == "not_started" and back["completed_at"] is None
    assert patch("done").status_code == 422


def test_progress_counts_only_scheduled_items_and_excludes_skipped(api):
    d = create(api)
    first, second, deferred = d["items"]
    base = f"/roadmaps/{d['id']}"
    set_status = lambda item, s: api.client.patch(f"{base}/items/{item['id']}", json={"status": s})  # noqa: E731
    prog = lambda: api.client.get(f"{base}/progress").json()  # noqa: E731

    set_status(first, "completed")
    assert prog() == {"total_items": 2, "completed_items": 1, "in_progress_items": 0, "remaining_items": 1,
                      "skipped_items": 0, "deferred_items": 1, "percent_complete": 50.0}
    set_status(second, "in_progress")
    assert (prog()["in_progress_items"], prog()["remaining_items"]) == (1, 0)
    set_status(second, "skipped")
    assert prog() == {"total_items": 1, "completed_items": 1, "in_progress_items": 0, "remaining_items": 0,

                      "skipped_items": 1, "deferred_items": 1, "percent_complete": 100.0}
    assert api.client.get(base).json()["progress"] == prog()
    assert set_status(deferred, "completed").status_code == 400                    # no schedule to track
    assert prog()["completed_items"] == 1


def test_item_must_belong_to_that_roadmap(api):
    one, two = create(api), create(api)
    other_items_url = f"/roadmaps/{one['id']}/items/{two['items'][0]['id']}"
    assert api.client.patch(other_items_url, json={"status": "completed"}).status_code == 404
    assert api.client.patch(f"/roadmaps/{one['id']}/items/9999", json={"status": "completed"}).status_code == 404


def test_delete_removes_roadmap_and_items_but_not_module4_data(api):
    d = create(api)
    assert api.client.delete(f"/roadmaps/{d['id']}").status_code == 204
    assert api.client.get(f"/roadmaps/{d['id']}").status_code == 404 and api.client.get("/roadmaps").json() == []
    with api.Session() as s:
        assert s.query(RoadmapItem).count() == 0
        assert s.query(SkillGapAnalysis).count() == 1 and s.query(SkillGapResult).count() == 4


def test_source_analysis_changed_flag(api):
    d = create(api)
    with api.Session() as s:                                   # Module 4 data changes after the roadmap was built
        s.query(SkillGapResult).filter(SkillGapResult.priority == P.high).first().priority = P.low
        s.commit()
    assert api.client.get(f"/roadmaps/{d['id']}").json()["source_analysis_changed"] is True
    fresh = create(api)                                        # built from the new data, so it is up to date
    assert api.client.get(f"/roadmaps/{fresh['id']}").json()["source_analysis_changed"] is False



def test_roadmap_survives_deletion_of_its_analysis_and_is_flagged(api):
    d = create(api)
    with api.Session() as s:
        s.delete(s.get(SkillGapAnalysis, api.aid))
        s.commit()
    got = api.client.get(f"/roadmaps/{d['id']}").json()
    assert got["analysis_id"] is None and got["source_analysis_changed"] is True and len(got["items"]) == 3