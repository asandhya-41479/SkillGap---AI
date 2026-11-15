"""Module 5 fix: generating a new roadmap for the same analysis supersedes the previous active one, so there is
always exactly one active roadmap per analysis (Modules 6 and 7 read that one)."""
from app.models.roadmap import Roadmap, RoadmapLifecycle
from tests.test_roadmap_api import api, create  # noqa: F401  (api is a pytest fixture)


def active_ids(api):
    with api.Session() as s:
        return [r.id for r in s.query(Roadmap).filter(Roadmap.lifecycle == RoadmapLifecycle.active)]


def test_new_roadmap_supersedes_the_previous_active_one(api):
    first = create(api)
    second = create(api)
    assert active_ids(api) == [second["id"]]
    old = api.client.get(f"/roadmaps/{first['id']}").json()
    assert old["lifecycle"] == "superseded"                       # kept as an older version, not deleted
    assert [r["id"] for r in api.client.get("/roadmaps").json()] == [second["id"], first["id"]]


def test_progress_can_only_be_tracked_on_the_active_roadmap(api):
    first = create(api)
    create(api)
    r = api.client.patch(f"/roadmaps/{first['id']}/items/{first['items'][0]['id']}", json={"status": "completed"})
    assert r.status_code == 409                                    # no more "progress that is not counted"


def test_other_users_roadmaps_are_not_superseded(api):
    mine = create(api)
    api.as_user(api.other)
    assert api.client.post("/roadmaps", json={"analysis_id": api.aid, "hours_per_week": 6,
                                               "duration_weeks": 4}).status_code == 404
    api.as_user(api.uid)
    assert active_ids(api) == [mine["id"]]
