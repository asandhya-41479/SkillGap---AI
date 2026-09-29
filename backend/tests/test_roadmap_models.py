"""Module 5 Step 2 tests: roadmap models, constraints, cascades, and schemas.

Runs on in-memory SQLite (no Postgres/Gemini needed). Foreign keys are enabled
explicitly because SQLite ignores them by default.
"""
import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import github_connection, job, oauth_state, roadmap, skill, skill_gap, user  # noqa: F401
from app.models.job import Importance, JobDescription, JobRequirement
from app.models.roadmap import (
    EffortSize,
    GenerationSource,
    ItemStatus,
    Roadmap,
    RoadmapItem,
)
from app.models.skill_gap import (
    MatchClassification,
    PriorityLevel,
    SkillGapAnalysis,
)
from app.models.user import User
from app.schemas.roadmap import (
    RoadmapCreate,
    RoadmapDetailResponse,
    RoadmapItemResponse,
    RoadmapItemStatusUpdate,

)


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def make_user(db, email="a@example.com"):
    u = User(name="A", email=email, password_hash="x")
    db.add(u)
    db.flush()
    return u


def make_analysis(db, u):
    j = JobDescription(user_id=u.id, target_role="AI Engineer", raw_description="...")
    db.add(j)
    db.flush()
    req = JobRequirement(job_description_id=j.id, skill_name="Docker", importance=Importance.required)
    db.add(req)
    a = SkillGapAnalysis(user_id=u.id, job_description_id=j.id, overall_alignment_score=0.4)
    db.add(a)

    db.flush()
    return a, req


def make_roadmap(db, u, a=None, **kw):
    r = Roadmap(
        user_id=u.id,
        analysis_id=a.id if a else None,
        title="AI Engineer Roadmap",
        target_role="AI Engineer",
        hours_per_week=kw.get("hours_per_week", 10),
        duration_weeks=kw.get("duration_weeks", 8),
        capacity_hours=80,
    )
    db.add(r)
    db.flush()
    return r


def make_item(db, r, name="Docker", order=0, req=None, **kw):
    item = RoadmapItem(
        roadmap_id=r.id,
        job_requirement_id=req.id if req else None,
        skill_name=name,
        gap_classification=MatchClassification.gap,
        importance=Importance.required,
        priority=PriorityLevel.high,
        effort_size=EffortSize.medium,
        estimated_hours=14,
        order_index=order,
        **kw,
    )

    db.add(item)
    db.flush()
    return item


# ---------- Tables / defaults ----------

def test_tables_registered():
    assert "roadmaps" in Base.metadata.tables
    assert "roadmap_items" in Base.metadata.tables


def test_defaults(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    item = make_item(db, r)
    db.commit()
    assert r.generation_source == GenerationSource.rules_only
    assert r.lifecycle.value == "active"
    assert r.experience_level.value == "intermediate"
    assert item.status == ItemStatus.not_started
    assert item.is_scheduled is True and item.is_supplementary is False


def test_json_columns_roundtrip(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    item = make_item(
        db, r,
        prerequisites=["Python"],
        topics=["Routing", "Pydantic"],
        practical_tasks=[{"title": "Build API", "description": "Small REST API", "type": "exercise"}],

    )
    db.commit()
    db.expire_all()
    got = db.get(RoadmapItem, item.id)
    assert got.prerequisites == ["Python"]
    assert got.practical_tasks[0]["title"] == "Build API"


def test_items_ordered_by_order_index(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    make_item(db, r, "C", order=2)
    make_item(db, r, "A", order=0)
    make_item(db, r, "B", order=1)
    db.commit()
    db.refresh(r)
    assert [i.skill_name for i in r.items] == ["A", "B", "C"]


# ---------- Constraints ----------

def test_duplicate_skill_in_roadmap_rejected(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    make_item(db, r, "Docker", order=0)
    with pytest.raises(IntegrityError):
        make_item(db, r, "Docker", order=1)


def test_same_skill_allowed_in_different_roadmaps(db):
    u = make_user(db)
    r1, r2 = make_roadmap(db, u), make_roadmap(db, u)

    make_item(db, r1, "Docker")
    make_item(db, r2, "Docker")  # must not raise
    db.commit()


@pytest.mark.parametrize("hpw,weeks", [(0, 8), (41, 8), (10, 0), (10, 27)])
def test_out_of_range_constraints_rejected(db, hpw, weeks):
    u = make_user(db)
    with pytest.raises(IntegrityError):
        make_roadmap(db, u, hours_per_week=hpw, duration_weeks=weeks)


# ---------- Relationships / cascades ----------

def test_user_can_have_multiple_roadmaps(db):
    u = make_user(db)
    make_roadmap(db, u)
    make_roadmap(db, u)
    db.commit()
    assert db.query(Roadmap).filter_by(user_id=u.id).count() == 2


def test_deleting_roadmap_cascades_to_items(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    make_item(db, r)
    db.commit()
    db.delete(r)
    db.commit()
    assert db.query(RoadmapItem).count() == 0



def test_deleting_user_cascades_to_roadmaps(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    make_item(db, r)
    db.commit()
    db.query(User).filter_by(id=u.id).delete()  # bulk delete -> exercises DB-level ON DELETE CASCADE
    db.commit()
    assert db.query(Roadmap).count() == 0
    assert db.query(RoadmapItem).count() == 0


def test_deleting_analysis_keeps_roadmap(db):
    u = make_user(db)
    a, req = make_analysis(db, u)
    r = make_roadmap(db, u, a)
    make_item(db, r, req=req)
    db.commit()
    db.query(SkillGapAnalysis).filter_by(id=a.id).delete()
    db.commit()
    db.refresh(r)
    assert r.analysis_id is None  # SET NULL
    assert db.query(RoadmapItem).count() == 1


def test_deleting_requirement_keeps_item(db):
    u = make_user(db)
    a, req = make_analysis(db, u)
    r = make_roadmap(db, u, a)
    item = make_item(db, r, req=req)
    db.commit()
    db.query(JobRequirement).filter_by(id=req.id).delete()
    db.commit()

    db.refresh(item)
    assert item.job_requirement_id is None


def test_parent_roadmap_set_null_on_delete(db):
    u = make_user(db)
    parent = make_roadmap(db, u)
    child = make_roadmap(db, u)
    child.parent_roadmap_id = parent.id
    db.commit()
    db.query(Roadmap).filter_by(id=parent.id).delete()
    db.commit()
    db.refresh(child)
    assert child.parent_roadmap_id is None


# ---------- Schemas ----------

def test_create_schema_defaults():
    c = RoadmapCreate(analysis_id=1)
    assert (c.hours_per_week, c.duration_weeks) == (8, 8)
    assert c.experience_level.value == "intermediate"


@pytest.mark.parametrize("field,val", [("hours_per_week", 0), ("hours_per_week", 41),
                                       ("duration_weeks", 0), ("duration_weeks", 27)])
def test_create_schema_bounds(field, val):
    with pytest.raises(ValidationError):
        RoadmapCreate(analysis_id=1, **{field: val})


def test_status_update_rejects_unknown_value():

    RoadmapItemStatusUpdate(status="completed")
    with pytest.raises(ValidationError):
        RoadmapItemStatusUpdate(status="done")


def test_item_response_from_orm_and_detail_response(db):
    u = make_user(db)
    r = make_roadmap(db, u)
    make_item(
        db, r,
        prerequisites=["Python"], topics=["Routing"],
        practical_tasks=[{"title": "t", "description": "d", "type": "project_task"}],
        start_week=1, end_week=2, reason="why", milestone="m",
    )
    db.commit()
    db.refresh(r)
    item_resp = RoadmapItemResponse.model_validate(r.items[0])
    assert item_resp.priority == PriorityLevel.high
    assert item_resp.practical_tasks[0].type == "project_task"
    detail = RoadmapDetailResponse.model_validate(r)
    assert detail.items[0].skill_name == "Docker"
    assert detail.progress is None and detail.source_analysis_changed is False