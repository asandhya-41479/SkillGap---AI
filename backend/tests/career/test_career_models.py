"""Module 7: model tests on in-memory SQLite with the real Module 1-6 tables."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import sessionmaker

import app.models.career  # noqa: F401
from app.db.base import Base
from app.models.career import (
    ActionCategory, ActionPriority, ActionStatus, CareerAction, CareerPlan, CareerStatus,
    InterviewPrepItem, OpportunityMatch, OpportunitySource, PrepKind,
)
from app.models.job import JobDescription
from app.models.user import User


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def _fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()
    Base.metadata.drop_all(engine)


def _user_job(db, n=1):
    u = User(name=f"U{n}", email=f"u{n}@test.com", password_hash="x")
    db.add(u); db.flush()
    j = JobDescription(user_id=u.id, target_role="AI Engineer", raw_description="Python required")
    db.add(j); db.commit()
    return u, j


def _plan(db, u, j):
    p = CareerPlan(user_id=u.id, job_description_id=j.id, input_hash="a" * 64, target_role="AI Engineer",
                   career_status=CareerStatus.DEVELOPING, readiness_score=74, engine_version="1.0")
    db.add(p); db.commit()
    return p


def _action(u, j, p, key="docker:PROVE", active=True):
    return CareerAction(user_id=u.id, job_description_id=j.id, plan_id=p.id, action_key=key,
                        category=ActionCategory.PROVE, priority=ActionPriority.HIGH, priority_score=67,
                        title="Dockerize SkillGap AI", reason="Required skill + no solid evidence yet.",
                        reason_codes=["REQUIRED"], evidence_required=["Dockerfile"], skill_name="Docker",
                        is_active=active)


def test_defaults_and_relationship(db):
    u, j = _user_job(db); p = _plan(db, u, j)
    a = _action(u, j, p); db.add(a); db.commit(); db.refresh(a)
    assert a.status == ActionStatus.NOT_STARTED and a.explanation is None and a.created_at
    assert p.actions[0].id == a.id and p.status_criteria == [] and p.gemini_used is False


def test_one_active_action_per_key_per_job(db):
    u, j = _user_job(db); p = _plan(db, u, j)
    db.add(_action(u, j, p)); db.commit()
    db.add(_action(u, j, p))
    with pytest.raises(IntegrityError):
        db.commit()


def test_archived_history_and_other_users(db):
    u1, j1 = _user_job(db, 1); u2, j2 = _user_job(db, 2)
    p1, p2 = _plan(db, u1, j1), _plan(db, u2, j2)
    db.add_all([_action(u1, j1, p1, active=False), _action(u1, j1, p1, active=False),
                _action(u1, j1, p1), _action(u2, j2, p2)])
    db.commit()
    assert db.query(CareerAction).filter_by(user_id=u1.id).count() == 3


def test_invalid_enum_rejected(db):
    u, j = _user_job(db); p = _plan(db, u, j)
    a = _action(u, j, p); a.status = "MASTERED"; db.add(a)
    with pytest.raises((StatementError, LookupError)):
        db.commit()


def test_plan_delete_keeps_actions(db):
    u, j = _user_job(db); p = _plan(db, u, j)
    db.add(_action(u, j, p)); db.commit()
    db.delete(p); db.commit()
    assert db.query(CareerAction).one().plan_id is None


def test_interview_and_opportunity_rows(db):
    u, j = _user_job(db)
    db.add(InterviewPrepItem(user_id=u.id, job_description_id=j.id, kind=PrepKind.PROJECT,
                             topic_id="proj_validation", topic="Gemini output validation",
                             fact_id="F_GEMINI_VALIDATION", priority=ActionPriority.MEDIUM, why="You built this."))
    db.add(OpportunityMatch(user_id=u.id, source=OpportunitySource.SAVED_JOB, job_description_id=j.id,
                            text_hash="b" * 64, coverage_pct=78.0, breakdown={"strong": ["Python"]}))
    db.commit()
    assert db.query(InterviewPrepItem).one().questions == []
    assert db.query(OpportunityMatch).one().company is None


def test_deleting_job_removes_its_career_data(db):
    u, j = _user_job(db); p = _plan(db, u, j)
    db.add(_action(u, j, p)); db.commit()
    db.delete(j); db.commit()
    assert db.query(CareerPlan).count() == 0 and db.query(CareerAction).count() == 0
