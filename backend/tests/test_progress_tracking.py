"""Module 6 Step 3 tests: roadmap item progress (status, notes, practical task, timestamps, ownership).
Reuses the real-router / in-memory-DB / fake-login fixture from test_roadmap_api.py."""
import pytest

from app.dependencies.auth import get_current_user
from app.models.roadmap import Roadmap, RoadmapLifecycle
from tests.test_roadmap_api import api, create  # noqa: F401  (api is a pytest fixture)

OLD, NEW = "items/{}", "items/{}/progress"   # Module 5 path and the Module 6 alias


@pytest.fixture()
def item(api):
    d = create(api)
    first, second, deferred = d["items"]
    base = f"/roadmaps/{d['id']}"
    return type("Ctx", (), dict(
        base=base, first=first, second=second, deferred=deferred,
        patch=lambda self, it, path=OLD, **json: api.client.patch(f"{base}/{path.format(it['id'])}", json=json),
        progress=lambda self: api.client.get(f"{base}/progress").json(),
        item=lambda self, it: next(i for i in api.client.get(base).json()["items"] if i["id"] == it["id"]),
    ))()


@pytest.mark.parametrize("path", [OLD, NEW])
def test_all_four_states_work_on_both_paths(item, path):
    for s in ["in_progress", "completed", "skipped", "not_started"]:
        r = item.patch(item.first, path, status=s)
        assert r.status_code == 200 and r.json()["status"] == s


def test_completed_at_and_updated_at(item):

    assert item.patch(item.first, status="in_progress").json()["completed_at"] is None
    done = item.patch(item.first, status="completed").json()
    assert done["completed_at"] and done["updated_at"]
    again = item.patch(item.first, status="completed").json()
    assert again["completed_at"] == done["completed_at"]                       # not re-stamped
    assert item.patch(item.first, status="skipped").json()["completed_at"] is None
    assert item.patch(item.first, status="in_progress").json()["completed_at"] is None
    redone = item.patch(item.first, status="completed").json()
    assert redone["completed_at"] and redone["updated_at"] >= done["updated_at"]


def test_progress_percentage_follows_every_state(item):
    pct = lambda: item.progress()["percent_complete"]  # noqa: E731
    assert pct() == 0.0
    item.patch(item.first, status="in_progress")
    assert (pct(), item.progress()["in_progress_items"]) == (0.0, 1)
    item.patch(item.first, status="completed")
    assert pct() == 50.0
    item.patch(item.second, status="skipped")
    assert (pct(), item.progress()["total_items"]) == (100.0, 1)               # skipped leaves the denominator
    item.patch(item.second, status="not_started")
    assert pct() == 50.0
    item.patch(item.first, status="not_started")
    assert pct() == 0.0


def test_practical_task_flag_rules(item):
    assert item.item(item.first)["practical_done"] is False
    r = item.patch(item.first, practical_done=True)                            # still not_started
    assert r.status_code == 400
    assert item.item(item.first)["practical_done"] is False
    assert item.patch(item.first, status="in_progress", practical_done=True).json()["practical_done"] is True

    assert item.patch(item.first, status="completed").json()["practical_done"] is True       # kept on completion
    assert item.patch(item.first, status="in_progress").json()["practical_done"] is True     # kept when reopened
    assert item.patch(item.first, practical_done=False).json()["practical_done"] is False
    item.patch(item.first, practical_done=True)
    assert item.patch(item.first, status="not_started").json()["practical_done"] is False    # restart clears it
    item.patch(item.first, status="in_progress", practical_done=True)
    assert item.patch(item.first, status="skipped").json()["practical_done"] is False        # skip clears it
    assert item.patch(item.first, status="skipped", practical_done=True).status_code == 400


def test_practical_flag_does_not_change_status_or_progress(item):
    item.patch(item.first, status="in_progress", practical_done=True)
    assert item.item(item.first)["status"] == "in_progress"
    assert item.progress()["completed_items"] == 0                             # practical task is not a completion


def test_notes_set_trim_clear_and_survive_status_changes(item):
    assert item.patch(item.first, notes="  did lab 1  ").json()["notes"] == "did lab 1"
    assert item.patch(item.first, status="completed").json()["notes"] == "did lab 1"        # untouched by status-only call
    assert item.patch(item.first, notes="").json()["notes"] is None
    item.patch(item.first, notes="x")
    assert item.patch(item.first, notes=None).json()["notes"] is None          # explicit null clears too
    assert item.patch(item.first, notes="a" * 501).status_code == 422
    assert item.patch(item.first, notes="a" * 500).status_code == 200


def test_one_call_can_change_everything_and_empty_calls_are_rejected(item):
    r = item.patch(item.first, status="completed", practical_done=True, notes="shipped").json()
    assert (r["status"], r["practical_done"], r["notes"]) == ("completed", True, "shipped")
    for bad in [{}, {"status": None}, {"practical_done": None}, {"status": "done"}, {"practical_done": "maybe"}]:
        assert item.patch(item.first, **bad).status_code == 422, bad



def test_deferred_item_cannot_be_tracked_at_all(item):
    for body in [{"status": "completed"}, {"notes": "hi"}, {"practical_done": True}]:
        assert item.patch(item.deferred, **body).status_code == 400


def test_superseded_roadmap_is_read_only(api, item):
    with api.Session() as s:
        r = s.query(Roadmap).one()
        r.lifecycle = RoadmapLifecycle.superseded
        s.commit()
    assert item.patch(item.first, notes="x").status_code == 409
    assert item.patch(item.first, status="completed").status_code == 409


@pytest.mark.parametrize("path", [OLD, NEW])
def test_other_users_get_404_and_nothing_changes(api, item, path):
    api.as_user(api.other)
    assert item.patch(item.first, path, status="completed", notes="hack").status_code == 404
    api.as_user(api.uid)
    got = item.item(item.first)
    assert (got["status"], got["notes"], got["practical_done"]) == ("not_started", None, False)


def test_item_must_belong_to_the_roadmap_in_the_url(api, item):
    other = create(api)
    r = api.client.patch(f"/roadmaps/{other['id']}/items/{item.first['id']}/progress", json={"status": "completed"})
    assert r.status_code == 404
    assert item.item(item.first)["status"] == "not_started"


def test_login_is_required_on_the_progress_path(api, item):

    api.app.dependency_overrides.pop(get_current_user)
    assert api.client.patch(f"{item.base}/items/{item.first['id']}/progress", json={"notes": "x"}).status_code in (401, 403)


def test_adapting_a_roadmap_keeps_notes_and_practical_flags(api, item):
    item.patch(item.first, status="completed", practical_done=True, notes="finished lab")
    item.patch(item.second, status="in_progress", practical_done=True, notes="halfway")
    new = api.client.post(f"{item.base}/regenerate", json={"mode": "adapt"})
    assert new.status_code == 201
    got = {i["skill_name"]: i for i in new.json()["items"]}
    done, doing = got[item.first["skill_name"]], got[item.second["skill_name"]]
    assert (done["status"], done["practical_done"], done["notes"]) == ("completed", True, "finished lab")
    assert (doing["status"], doing["practical_done"], doing["notes"]) == ("in_progress", True, "halfway")
    assert done["completed_at"]


def test_fresh_regenerate_starts_clean(api, item):
    item.patch(item.first, status="completed", practical_done=True, notes="old")
    new = api.client.post(f"{item.base}/regenerate", json={"mode": "fresh"}).json()
    assert all(i["notes"] is None and i["practical_done"] is False and i["status"] == "not_started"
               for i in new["items"])