"""Module 5 Step 5 tests: generate_and_store (real DB models, fake Gemini, no key, no network)."""
import pytest
from fastapi import HTTPException

from app.core.roadmap_config import NOTE_NO_GAPS
from app.models.roadmap import GenerationSource as S, ItemStatus, Roadmap, RoadmapItem
from app.models.skill import SkillLevel as L
from app.models.skill_gap import AnalysisStatus, MatchClassification as C, PriorityLevel as P
from app.schemas.roadmap import RoadmapCreate, RoadmapDetailResponse
from app.services.roadmap.gap_reader import load_plan_input
from app.services.roadmap.plan_types import RoadmapConstraints
from app.services.roadmap.planner import plan_roadmap
from app.services.roadmap.roadmap_service import generate_and_store
from tests.test_roadmap_llm import Fake, good_reply
from tests.test_roadmap_rule_engine import db, seed  # noqa: F401  (db is a pytest fixture)


def make(db, **over):
    u, other, a = seed(db)
    return u, other, a, RoadmapCreate(analysis_id=a.id, hours_per_week=6, duration_weeks=4, **over)


def skeleton(r):
    return [(i.skill_name, i.priority, i.gap_classification, i.importance, i.effort_size, i.estimated_hours,
             i.is_scheduled, i.start_week, i.end_week, i.order_index, i.prerequisites, i.job_requirement_id)
            for i in r.items]


def test_roadmap_is_stored_with_plan_skeleton_and_gemini_wording(db):
    u, _, a, data = make(db)
    r = generate_and_store(db, u.id, data, call=Fake(good_reply))
    plan = plan_roadmap(load_plan_input(db, u.id, a.id), RoadmapConstraints(6, 4, L.intermediate))

    assert (r.user_id, r.analysis_id, r.generation_source) == (u.id, a.id, S.gemini)
    assert r.title == "AI Engineer Roadmap" and r.target_role == "AI Engineer" and r.lifecycle.value == "active"
    assert (r.hours_per_week, r.duration_weeks, r.capacity_hours) == (6, 4, 24.0)
    assert r.total_estimated_hours == plan.scheduled_hours and r.summary and r.feasibility_note == plan.feasibility_note
    assert [(i.skill_name, i.priority, i.estimated_hours, i.start_week, i.end_week, i.order_index) for i in r.items] == \
        [(p.skill_name, p.priority, p.estimated_hours, p.start_week, p.end_week, p.order_index) for p in plan.items]
    done = [i for i in r.items if i.is_scheduled]
    assert done and all(i.topics and i.practical_tasks and i.project_task and i.milestone for i in done)
    assert all(i.status == ItemStatus.not_started for i in r.items)
    assert db.query(RoadmapItem).filter_by(roadmap_id=r.id).count() == len(plan.items)


def test_deferred_items_are_stored_without_a_schedule_and_with_the_reason(db):
    u, _, _, data = make(db)
    r = generate_and_store(db, u.id, data, call=Fake(good_reply))
    deferred = [i for i in r.items if not i.is_scheduled]
    assert deferred                                           # 24 h budget cannot hold Kubernetes
    for i in deferred:
        assert i.start_week is None and i.end_week is None and i.topics == [] and i.practical_tasks == []
        assert i.project_task is None and i.milestone is None and "fit" in i.reason.lower()
    assert r.total_estimated_hours == sum(i.estimated_hours for i in r.items if i.is_scheduled)


def test_gemini_down_still_stores_a_complete_rules_only_roadmap(db):
    u, _, _, data = make(db)
    down = generate_and_store(db, u.id, data, call=Fake(RuntimeError("503"), RuntimeError("503")))
    assert down.generation_source == S.rules_only and down.summary
    assert all(i.topics and i.practical_tasks for i in down.items if i.is_scheduled)
    up = generate_and_store(db, u.id, data, call=Fake(good_reply))
    assert skeleton(down) == skeleton(up)                     # Gemini never changes the plan


def test_roadmap_serialises_with_the_step_2_response_schema(db):
    u, _, _, data = make(db)
    r = generate_and_store(db, u.id, data, call=Fake(good_reply))
    out = RoadmapDetailResponse.model_validate(r)
    assert out.id == r.id and len(out.items) == len(r.items)
    assert out.items[0].practical_tasks[0].title


def test_snapshot_records_the_verified_gaps(db):
    u, _, _, data = make(db)
    snap = generate_and_store(db, u.id, data, call=Fake(good_reply)).input_snapshot
    assert {g["skill"] for g in snap["gaps"]} == {"FastAPI", "Docker", "Kubernetes"}    # strong Python excluded
    assert {"gap", "transferable"} == {g["classification"] for g in snap["gaps"]}
    assert "Python" in snap["known_skills"]


def test_constraints_and_style_are_applied(db):
    u, _, _, data = make(db, experience_level=L.beginner, learning_style="hands_on")
    fake = Fake(good_reply)
    r = generate_and_store(db, u.id, data, call=fake)
    assert r.experience_level == L.beginner and r.learning_style.value == "hands_on"
    assert '"learning_style": "hands_on"' in fake.prompts[0] and '"learner_level": "beginner"' in fake.prompts[0]
    assert next(i for i in r.items if i.skill_name == "Docker").estimated_hours == 18    # 14 h x 1.25 beginner


def test_missing_foreign_or_failed_analysis_stores_nothing(db):
    u, other, a, data = make(db)
    fake = Fake(good_reply)
    for uid, d, code in [(other.id, data, 404), (u.id, RoadmapCreate(analysis_id=9999), 404)]:
        with pytest.raises(HTTPException) as e:
            generate_and_store(db, uid, d, call=fake)
        assert e.value.status_code == code
    a.status = AnalysisStatus.failed
    db.commit()
    with pytest.raises(HTTPException) as e:
        generate_and_store(db, u.id, data, call=fake)
    assert e.value.status_code == 400 and fake.prompts == [] and db.query(Roadmap).count() == 0


def test_analysis_without_gaps_gives_an_empty_roadmap_and_no_gemini_call(db):
    u, _, a, data = make(db)
    for res in a.results:
        res.classification, res.priority = C.strong, P.none
    db.commit()
    fake = Fake(good_reply)
    r = generate_and_store(db, u.id, data, call=fake)
    assert r.items == [] and r.feasibility_note == NOTE_NO_GAPS and r.total_estimated_hours == 0
    assert r.generation_source == S.rules_only and fake.prompts == []


def test_failed_save_leaves_nothing_behind(db, monkeypatch):
    u, _, _, data = make(db)

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(db, "commit", boom)
    with pytest.raises(RuntimeError):
        generate_and_store(db, u.id, data, call=Fake(good_reply))
    assert db.query(Roadmap).count() == 0 and db.query(RoadmapItem).count() == 0