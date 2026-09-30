"""Module 5 Step 3 tests: deterministic roadmap rule engine and Module 4 reader.

No Gemini, no Postgres. The reader tests use in-memory SQLite with real Module 3/4 models.
"""
import itertools

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core import roadmap_config as cfg
from app.db.base import Base
from app.models import github_connection, job, oauth_state, roadmap, skill, skill_gap, user  # noqa: F401
from app.models.job import Importance as I
from app.models.job import JobDescription, JobRequirement
from app.models.roadmap import EffortSize
from app.models.skill import SkillLevel as L
from app.models.skill import UserSkill
from app.models.skill_gap import (
    AnalysisStatus,
    MatchClassification as C,
    PriorityLevel as P,
    SkillGapAnalysis,
    SkillGapResult,
)
from app.models.user import User
from app.services.roadmap.dependency_graph import find_cycle, skill_key
from app.services.roadmap.effort import estimate_hours, reduced_hours
from app.services.roadmap.gap_reader import load_plan_input
from app.services.roadmap.plan_types import GapInput, PlanInput, RoadmapConstraints
from app.services.roadmap.planner import plan_roadmap



# ---------------------------------------------------------------- helpers

def g(name, imp=I.required, cls=C.gap, pri=P.high, matched=None, sim=0.1, req_id=None):
    return GapInput(req_id, name, imp, cls, pri, sim, matched)


def plan(gaps, known=(), hpw=10, weeks=8, level=L.intermediate):
    return plan_roadmap(PlanInput("AI Engineer", list(gaps), list(known)), RoadmapConstraints(hpw, weeks, level))


def names(p, scheduled_only=False):
    items = p.scheduled_items if scheduled_only else p.items
    return [i.skill_name for i in items]


def by_name(p, name):
    return next(i for i in p.items if i.skill_name == name)


# ---------------------------------------------------------------- static rules

def test_static_dependency_graph_is_acyclic():
    assert find_cycle() is None


def test_dependency_keys_are_normalized_keys():
    for k, deps in cfg.DEPENDENCIES.items():
        assert skill_key(k) == k, k
        for p in deps.get("hard", []) + deps.get("soft", []):
            assert skill_key(p) == p, p



@pytest.mark.parametrize("raw,expected", [
    ("Postgres", "postgresql"), ("REST APIs", "rest api"), ("react.js", "react"),
    ("sklearn", "scikit-learn"), ("CI/CD", "ci/cd"), ("  FastAPI ", "fastapi"),
])
def test_skill_key_aliases(raw, expected):
    assert skill_key(raw) == expected


@pytest.mark.parametrize("size,cls,level,expected", [
    (EffortSize.medium, C.gap, L.intermediate, 14),
    (EffortSize.medium, C.partial, L.intermediate, 7),
    (EffortSize.medium, C.transferable, L.intermediate, 11),   # 10.5 rounds half-up
    (EffortSize.large, C.gap, L.beginner, 35),
    (EffortSize.small, C.gap, L.beginner, 8),                  # 7.5 rounds half-up
    (EffortSize.small, C.gap, L.advanced, 5),
    (EffortSize.small, C.partial, L.advanced, 2),              # floor at MIN_ITEM_HOURS
])
def test_estimate_hours(size, cls, level, expected):
    assert estimate_hours(size, cls, level) == expected


def test_reduced_hours_has_floor():
    assert reduced_hours(14) == 8
    assert reduced_hours(2) == 2


# ---------------------------------------------------------------- filtering

def test_strong_and_none_priority_are_not_scheduled():
    p = plan([g("Docker"), g("Git", cls=C.strong, pri=P.none), g("SQL", pri=P.none)])

    assert names(p) == ["Docker"]


def test_no_gaps_returns_empty_plan_with_message():
    p = plan([g("Git", cls=C.strong, pri=P.none)])
    assert p.items == [] and p.has_gaps is False
    assert p.feasibility_note == cfg.NOTE_NO_GAPS


def test_alias_duplicates_collapse_keeping_most_important():
    p = plan([g("Postgres", imp=I.preferred, pri=P.medium), g("PostgreSQL", imp=I.required, pri=P.high)],
             known=["SQL"])
    assert names(p) == ["PostgreSQL"]
    assert p.items[0].priority == P.high


# ---------------------------------------------------------------- prerequisites

def test_known_prerequisite_is_not_retaught():
    p = plan([g("FastAPI")], known=["Python"])
    assert names(p) == ["FastAPI"]
    assert p.items[0].satisfied_prerequisites == ["Python"]
    assert p.items[0].prerequisites == []


def test_missing_hard_prerequisite_becomes_small_supplementary_item():
    p = plan([g("FastAPI")], known=[])
    py = by_name(p, "Python")
    assert py.is_supplementary and py.effort_size == EffortSize.small
    assert py.job_requirement_id is None and py.gap_classification is None and py.importance is None
    assert py.priority == P.high                      # inherited from FastAPI
    assert "prerequisite for FastAPI" in py.reason

    assert names(p).index("Python") < names(p).index("FastAPI")
    assert by_name(p, "FastAPI").prerequisites == ["Python"]


def test_transitive_supplementary_chain_is_ordered():
    p = plan([g("RAG")], known=[])
    order = names(p)
    assert [n for n in order if n in {"Python", "Machine Learning", "Embeddings", "RAG"}] == \
        ["Python", "Machine Learning", "Embeddings", "RAG"]
    assert all(by_name(p, n).is_supplementary for n in ["Python", "Machine Learning", "Embeddings"])
    assert not by_name(p, "RAG").is_supplementary


def test_module4_priority_is_never_changed_for_real_gaps():
    # SQL is LOW but a hard prerequisite of a HIGH gap: it is ordered earlier, displayed as LOW.
    p = plan([g("PostgreSQL", pri=P.high), g("SQL", imp=I.optional, pri=P.low)], known=[])
    assert by_name(p, "SQL").priority == P.low
    assert by_name(p, "PostgreSQL").priority == P.high
    assert names(p).index("SQL") < names(p).index("PostgreSQL")
    assert "Also a prerequisite for PostgreSQL" in by_name(p, "SQL").reason


def test_soft_prerequisite_only_orders_never_adds():
    only_fastapi = plan([g("FastAPI")], known=["Python"])
    assert "REST API" not in names(only_fastapi)
    # REST API is optional/low, FastAPI required/high: only the soft edge can put REST API first.
    both = plan([g("FastAPI"), g("REST API", imp=I.optional, pri=P.low)], known=["Python"], hpw=40, weeks=8)
    assert names(both).index("REST API") < names(both).index("FastAPI")


def test_hard_prerequisite_precedes_dependent_even_when_less_important():
    # Docker (required) is listed first by importance, but Kubernetes hard-depends on it being

    # earlier; here the *prerequisite* is the less important one.
    p = plan([g("Kubernetes"), g("Docker", imp=I.optional, pri=P.low)], known=[], hpw=40, weeks=8)
    assert names(p).index("Docker") < names(p).index("Kubernetes")
    p2 = plan([g("Deep Learning"), g("Machine Learning", imp=I.preferred, pri=P.medium)], known=["Python"],
              hpw=40, weeks=8)
    assert names(p2).index("Machine Learning") < names(p2).index("Deep Learning")


def test_unknown_skill_defaults_to_medium_with_no_edges():
    p = plan([g("Zylophone Framework")], known=[])
    it = p.items[0]
    assert it.effort_size == EffortSize.medium and it.prerequisites == []
    assert it.estimated_hours == 14


# ---------------------------------------------------------------- ordering

def test_priority_then_importance_ordering_for_independent_skills():
    p = plan([
        g("Vue", imp=I.preferred, pri=P.medium),
        g("Django", imp=I.required, pri=P.high),
        g("CSS", imp=I.optional, pri=P.low),
        g("Git", imp=I.required, pri=P.high),
    ], known=["Python", "JavaScript"], hpw=40, weeks=8)
    order = names(p)
    assert set(order[:2]) == {"Django", "Git"}
    assert order.index("Vue") < order.index("CSS")


def test_partial_and_transferable_cost_less_than_full_gap():
    p = plan([g("Docker", cls=C.gap), g("Vue", cls=C.partial, pri=P.medium, imp=I.preferred),
              g("Django", cls=C.transferable)], known=["Python", "JavaScript"], hpw=40, weeks=8)

    assert by_name(p, "Docker").estimated_hours == 14
    assert by_name(p, "Vue").estimated_hours == 7
    assert by_name(p, "Django").estimated_hours == 11


def test_experience_level_scales_hours():
    b = plan([g("Docker")], level=L.beginner).items[0].estimated_hours
    i = plan([g("Docker")], level=L.intermediate).items[0].estimated_hours
    a = plan([g("Docker")], level=L.advanced).items[0].estimated_hours
    assert b > i > a


# ---------------------------------------------------------------- time constraint

def test_time_budget_is_respected_and_deferrals_have_reasons():
    gaps = [g("Docker"), g("FastAPI"), g("PostgreSQL"), g("RAG"), g("AWS", imp=I.preferred, pri=P.medium)]
    p = plan(gaps, known=["Python", "SQL"], hpw=4, weeks=4)
    assert p.scheduled_hours <= p.capacity_hours * (1 + cfg.CAPACITY_TOLERANCE)
    assert p.deferred_items
    assert all(i.deferred_reason for i in p.deferred_items)
    assert p.feasibility_note == cfg.NOTE_TIME_INSUFFICIENT


def test_deferred_prerequisite_defers_dependents():
    # Python (35h beginner) cannot fit in 10h; FastAPI/Django depend on it.
    p = plan([g("Python"), g("FastAPI"), g("Django")], known=[], hpw=5, weeks=2, level=L.beginner)
    assert p.scheduled_items == []
    assert by_name(p, "FastAPI").deferred_reason.startswith("Depends on Python")


def test_high_priority_item_gets_reduced_scope_when_it_almost_fits():
    # capacity 10h -> allowed 11h; Docker needs 14h, reduced 8h fits.

    p = plan([g("Docker")], hpw=5, weeks=2)
    d = p.items[0]
    assert d.is_scheduled and d.reduced_scope and d.estimated_hours == 8
    assert "core topics" in d.reason
    assert p.feasibility_note == cfg.NOTE_TIME_INSUFFICIENT


def test_non_high_priority_is_deferred_not_reduced():
    p = plan([g("Docker", imp=I.preferred, pri=P.medium)], hpw=5, weeks=2)
    assert not p.items[0].is_scheduled and not p.items[0].reduced_scope


def test_small_independent_item_backfills_after_a_deferral():
    # allowed = 22h. Order: Docker(14) fits; AWS(28, medium) deferred; Git(6, low) still backfills.
    p = plan([g("Docker"), g("AWS", imp=I.preferred, pri=P.medium), g("Git", imp=I.optional, pri=P.low)],
             hpw=10, weeks=2)
    assert by_name(p, "Docker").is_scheduled
    assert not by_name(p, "AWS").is_scheduled
    assert by_name(p, "Git").is_scheduled


def test_supplementary_time_is_not_spent_when_dependent_is_deferred():
    p = plan([g("RAG")], known=[], hpw=2, weeks=2)   # far too little time
    assert p.scheduled_items == []
    assert names(p) == ["RAG"]                        # no orphan prerequisite items in the output


def test_supplementary_prerequisites_count_toward_the_budget():
    p = plan([g("FastAPI")], known=[], hpw=10, weeks=2)  # Python(6)+FastAPI(14)=20 <= 22
    assert names(p, scheduled_only=True) == ["Python", "FastAPI"]
    assert p.scheduled_hours == 20



def test_note_is_absent_when_plan_has_comfortable_buffer():
    p = plan([g("Git")], hpw=10, weeks=8)
    assert p.feasibility_note is None


def test_tight_but_complete_plan_gets_buffer_warning_not_insufficient_warning():
    p = plan([g("Docker"), g("FastAPI"), g("PostgreSQL")], known=["Python", "SQL"], hpw=10, weeks=5)
    # 14 + 14 + 14 = 42 of 50h = 84% -> no warning; use a tighter budget
    p2 = plan([g("Docker"), g("FastAPI"), g("PostgreSQL")], known=["Python", "SQL"], hpw=9, weeks=5)
    assert p.feasibility_note is None
    assert p2.feasibility_note and "little buffer" in p2.feasibility_note
    assert not p2.deferred_items


# ---------------------------------------------------------------- weeks

def test_week_allocation_sequential_and_shared():
    p = plan([g("Docker"), g("FastAPI")], known=["Python"], hpw=10, weeks=8)   # 14h + 14h at 10h/week
    a, b = p.items
    assert (a.start_week, a.end_week) == (1, 2)
    assert (b.start_week, b.end_week) == (2, 3)


def test_item_exactly_filling_a_week_moves_next_item_to_next_week():
    p = plan([g("Git"), g("NumPy")], known=["Python"], hpw=6, weeks=4)   # 6h each
    assert [(i.start_week, i.end_week) for i in p.items] == [(1, 1), (2, 2)]


# ---------------------------------------------------------------- invariants across a grid

SCENARIOS = {

    "ai_backend": ([g("FastAPI"), g("PostgreSQL"), g("Docker"), g("RAG"), g("CI/CD", imp=I.preferred, pri=P.medium),
                    g("AWS", imp=I.preferred, pri=P.medium), g("Kubernetes", imp=I.optional, pri=P.low)], ["Git"]),
    "ml": ([g("PyTorch"), g("NLP"), g("MLOps", imp=I.preferred, pri=P.medium), g("Deep Learning")], ["Python"]),
    "frontend": ([g("Next.js"), g("TypeScript"), g("React", cls=C.partial, pri=P.medium)], []),
    "cold_start": ([g("LangChain"), g("RAG"), g("Vector Databases")], []),
}


@pytest.mark.parametrize("scenario,hpw,weeks,level", list(itertools.product(
    SCENARIOS, [2, 6, 10, 40], [2, 8, 26], [L.beginner, L.intermediate, L.advanced])))
def test_invariants(scenario, hpw, weeks, level):
    gaps, known = SCENARIOS[scenario]
    p = plan(gaps, known, hpw, weeks, level)
    allowed = hpw * weeks * (1 + cfg.CAPACITY_TOLERANCE)

    assert p.scheduled_hours <= allowed + 1e-9
    assert [i.order_index for i in p.items] == list(range(len(p.items)))
    assert len({i.skill_key for i in p.items}) == len(p.items)

    pos = {i.skill_name: i.order_index for i in p.items}
    last_start = 0
    for it in p.items:
        for pre in it.prerequisites:                     # prerequisites always come earlier
            assert pos[pre] < it.order_index, (it.skill_name, pre)
        if it.is_scheduled:
            assert 1 <= it.start_week <= it.end_week <= weeks
            assert it.start_week >= last_start           # weeks never go backwards
            last_start = it.start_week
        else:
            assert it.start_week is None and it.end_week is None and it.deferred_reason
    # a scheduled item never depends (hard) on something that was deferred
    sched = {i.skill_name for i in p.scheduled_items}

    for it in p.scheduled_items:
        for pre in it.prerequisites:
            assert pre in sched or not _is_hard(it.skill_key, pre), (it.skill_name, pre)


def _is_hard(key, prereq_name):
    return skill_key(prereq_name) in cfg.DEPENDENCIES.get(key, {}).get("hard", [])


def test_planning_is_deterministic():
    gaps, known = SCENARIOS["ai_backend"]
    assert plan(gaps, known) == plan(list(reversed(gaps)), list(reversed(known)))


@pytest.mark.parametrize("hpw,weeks", [(0, 8), (41, 8), (10, 0), (10, 27)])
def test_invalid_constraints_raise(hpw, weeks):
    with pytest.raises(ValueError):
        plan([g("Docker")], hpw=hpw, weeks=weeks)


# ---------------------------------------------------------------- reasons

def test_reason_reflects_classification_and_module4_data():
    p = plan([g("FastAPI", cls=C.transferable, matched="Flask"), g("Docker", imp=I.preferred, pri=P.medium),
              g("PostgreSQL", cls=C.partial, matched="SQL")], known=["Python", "SQL"], hpw=40, weeks=8)
    assert "related skills (Flask) that transfer" in by_name(p, "FastAPI").reason
    assert by_name(p, "Docker").reason.startswith("Preferred by the target role and not currently demonstrated")
    assert "partially covers it through SQL" in by_name(p, "PostgreSQL").reason


# ---------------------------------------------------------------- reader (real Module 3/4 models)


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


def seed(db):
    u = User(name="A", email="a@example.com", password_hash="x")
    other = User(name="B", email="b@example.com", password_hash="x")
    db.add_all([u, other])
    db.flush()
    py = UserSkill(user_id=u.id, skill_name="Python")
    sql = UserSkill(user_id=u.id, skill_name="SQL")
    flask = UserSkill(user_id=u.id, skill_name="Flask")
    db.add_all([py, sql, flask])
    j = JobDescription(user_id=u.id, target_role="AI Engineer", raw_description="...")
    db.add(j)
    db.flush()
    reqs = {n: JobRequirement(job_description_id=j.id, skill_name=n, importance=imp)
            for n, imp in [("Python", I.required), ("FastAPI", I.required), ("Docker", I.required),
                           ("Kubernetes", I.optional)]}
    db.add_all(reqs.values())
    a = SkillGapAnalysis(user_id=u.id, job_description_id=j.id, overall_alignment_score=40.0)
    db.add(a)

    db.flush()
    rows = [
        ("Python", C.strong, P.none, py, 0.95),
        ("FastAPI", C.transferable, P.high, flask, 0.5),
        ("Docker", C.gap, P.high, None, 0.05),
        ("Kubernetes", C.gap, P.low, None, 0.04),
    ]
    for name, cls, pri, matched, sim in rows:
        db.add(SkillGapResult(analysis_id=a.id, job_requirement_id=reqs[name].id,
                              matched_user_skill_id=matched.id if matched else None,
                              similarity_score=sim, classification=cls, priority=pri))
    db.commit()
    return u, other, a


def test_reader_builds_plan_input_from_module4_rows(db):
    u, _, a = seed(db)
    pi = load_plan_input(db, u.id, a.id)
    assert pi.target_role == "AI Engineer"
    assert {x.skill_name for x in pi.gaps} == {"FastAPI", "Docker", "Kubernetes"}   # strong Python excluded
    fastapi = next(x for x in pi.gaps if x.skill_name == "FastAPI")
    assert fastapi.classification == C.transferable and fastapi.priority == P.high
    assert fastapi.matched_skill_name == "Flask" and fastapi.importance == I.required
    assert {"Python", "SQL", "Flask"} <= set(pi.known_skills)


def test_reader_output_feeds_planner_end_to_end(db):
    u, _, a = seed(db)
    p = plan_roadmap(load_plan_input(db, u.id, a.id), RoadmapConstraints(10, 8, L.intermediate))
    assert "Python" not in [i.skill_name for i in p.items]   # known: never re-taught
    assert {i.skill_name for i in p.scheduled_items} == {"FastAPI", "Docker", "Kubernetes"} - \
        {i.skill_name for i in p.deferred_items}

    assert all(i.job_requirement_id for i in p.items)         # every real gap traces to Module 3


def test_reader_rejects_other_users_and_missing_analysis(db):
    u, other, a = seed(db)
    for uid, aid in [(other.id, a.id), (u.id, 9999)]:
        with pytest.raises(HTTPException) as e:
            load_plan_input(db, uid, aid)
        assert e.value.status_code == 404


def test_reader_rejects_failed_analysis(db):
    u, _, a = seed(db)
    a.status = AnalysisStatus.failed
    db.commit()
    with pytest.raises(HTTPException) as e:
        load_plan_input(db, u.id, a.id)
    assert e.value.status_code == 400