"""Module 6 Step 2 tests: new tables, new columns, constraints, cascades, schemas.
In-memory SQLite, foreign keys enabled (same pattern as test_roadmap_models.py)."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import github_connection, job, oauth_state, readiness, roadmap, skill, skill_gap, user  # noqa: F401
from app.models.readiness import (
    EvidenceKind, ProgressEvidence, ReadinessSnapshot, SnapshotTrigger, VerificationStatus,
)
from app.models.roadmap import RoadmapItem
from app.models.skill_gap import SkillGapResult
from app.models.user import User
from app.schemas.readiness import EvidenceCreate, ReadinessComponents, ReadinessMetrics
from app.schemas.roadmap import RoadmapItemResponse
from tests.test_roadmap_models import make_analysis, make_user


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


def snapshot(u, a, **kw):
    base = dict(user_id=u.id, job_description_id=a.job_description_id, analysis_id=a.id, score=45.0,
                formula_version="v1", input_fingerprint="abc", trigger=SnapshotTrigger.manual, metrics={})
    return ReadinessSnapshot(**{**base, **kw})


def test_new_tables_and_columns_exist(db):
    insp = inspect(db.get_bind())
    assert {"progress_evidence", "readiness_snapshots"} <= set(insp.get_table_names())
    assert {"notes", "practical_done"} <= {c["name"] for c in insp.get_columns("roadmap_items")}
    assert "evidence_adjusted" in {c["name"] for c in insp.get_columns("skill_gap_results")}


def test_existing_rows_get_safe_defaults(db):
    u = make_user(db)
    a, req = make_analysis(db, u)
    item = RoadmapItem(roadmap_id=_roadmap(db, u, a).id, skill_name="Docker", priority="high",
                       effort_size="small", estimated_hours=4, order_index=0)
    res = SkillGapResult(analysis_id=a.id, job_requirement_id=req.id, classification="gap")
    db.add_all([item, res])
    db.commit()
    assert item.notes is None and item.practical_done is False
    assert res.evidence_adjusted is False


def _roadmap(db, u, a):
    r = roadmap.Roadmap(user_id=u.id, analysis_id=a.id, title="t", target_role="AI Engineer",

                        hours_per_week=8, duration_weeks=8)
    db.add(r)
    db.flush()
    return r


def test_evidence_defaults_unique_and_cascade(db):
    u = make_user(db)
    db.add(ProgressEvidence(user_id=u.id, skill_name="Docker", kind=EvidenceKind.github_repo,
                            url="https://github.com/a/dockerized"))
    db.commit()
    e = db.query(ProgressEvidence).one()
    assert e.verification_status == VerificationStatus.linked   # never "verified" by default
    db.add(ProgressEvidence(user_id=u.id, skill_name="Docker", kind=EvidenceKind.project_url,
                            url="https://github.com/a/dockerized"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.delete(db.get(User, u.id))
    db.commit()
    assert db.query(ProgressEvidence).count() == 0


def test_evidence_survives_roadmap_item_deletion(db):
    u = make_user(db)
    a, _ = make_analysis(db, u)
    r = _roadmap(db, u, a)
    item = RoadmapItem(roadmap_id=r.id, skill_name="Docker", priority="high", effort_size="small",
                       estimated_hours=4, order_index=0)
    db.add(item)
    db.flush()
    db.add(ProgressEvidence(user_id=u.id, skill_name="Docker", kind=EvidenceKind.project_url,

                            url="https://example.com/p", roadmap_item_id=item.id))
    db.commit()
    db.delete(r)   # cascades to items
    db.commit()
    e = db.query(ProgressEvidence).one()
    assert e.roadmap_item_id is None


def test_snapshot_one_per_analysis_per_day(db):
    u = make_user(db)
    a, _ = make_analysis(db, u)
    db.add(snapshot(u, a))
    db.commit()
    db.add(snapshot(u, a))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    db.add(snapshot(u, a, snapshot_date=date.today() - timedelta(days=1)))   # other day is fine
    db.commit()
    assert db.query(ReadinessSnapshot).count() == 2


def test_snapshot_keeps_history_when_analysis_deleted(db):
    u = make_user(db)
    a, _ = make_analysis(db, u)
    db.add(snapshot(u, a, metrics={"alignment_pct": 62.0}))
    db.commit()
    db.delete(a)
    db.commit()
    s = db.query(ReadinessSnapshot).one()
    assert s.analysis_id is None and s.metrics["alignment_pct"] == 62.0 and s.score == 45.0



def test_snapshot_cascades_with_user(db):
    u = make_user(db)
    a, _ = make_analysis(db, u)
    db.add(snapshot(u, a))
    db.commit()
    db.delete(db.get(User, u.id))
    db.commit()
    assert db.query(ReadinessSnapshot).count() == 0


def test_evidence_schema_url_rules():
    ok = EvidenceCreate(skill_name="Docker", kind="github_repo", url="  https://github.com/a/b  ")
    assert ok.url == "https://github.com/a/b"
    for bad in ["http://github.com/a/b", "ftp://github.com/a/b", "https://exa mple.com/x", "javascript:alert(1)//"]:
        with pytest.raises(ValidationError):
            EvidenceCreate(skill_name="Docker", kind="project_url", url=bad)
    with pytest.raises(ValidationError):
        EvidenceCreate(skill_name="Docker", kind="blog", url="https://example.com/x")  # unknown kind


def test_schema_defaults():
    m = ReadinessMetrics()
    assert m.alignment_pct is None and m.high_priority_open == 0
    c = ReadinessComponents(alignment=0.5, required_coverage=0.5, evidence=0.0, gap_health=1.0, roadmap=None)
    assert c.roadmap is None


def test_roadmap_item_response_exposes_progress_fields(db):
    u = make_user(db)
    a, _ = make_analysis(db, u)
    item = RoadmapItem(roadmap_id=_roadmap(db, u, a).id, skill_name="Docker", priority="high",

                       effort_size="small", estimated_hours=4, order_index=0, notes="done lab 1",
                       practical_done=True)
    db.add(item)
    db.commit()
    out = RoadmapItemResponse.model_validate(item)
    assert out.notes == "done lab 1" and out.practical_done is True