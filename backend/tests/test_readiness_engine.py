"""Module 6 Step 5 tests: the readiness formula (pure, hand-computed) and the readiness API."""
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.readiness import router as readiness_router
from app.core import readiness_config as cfg
from app.dependencies.auth import get_current_user
from app.models.job import Importance as I
from app.models.readiness import EvidenceKind, ProgressEvidence, ReadinessSnapshot, VerificationStatus
from app.models.skill import UserSkill
from app.models.skill_gap import AnalysisStatus, MatchClassification as C, PriorityLevel as P, SkillGapAnalysis, SkillGapResult
from app.services.readiness_engine import Req, compute, label_for  
from tests.test_roadmap_api import api, create  # noqa: F401  (api is a pytest fixture)

# ---------- pure formula, numbers worked out by hand ----------
# Req weights: required 2, preferred 1, optional 0.5. Credits: strong 1, partial .5, transferable .25, gap 0.
SCENARIO = [Req("Python", I.required, C.strong, P.none), Req("FastAPI", I.required, C.gap, P.high),
            Req("Docker", I.preferred, C.gap, P.medium), Req("SQL", I.optional, C.partial, P.low)]


def test_scenario_a_no_evidence_no_roadmap():
    # sum(w)=5.5  A=2.25/5.5  C=1/2  E=0  G=1-2/5.5   weights without roadmap: .30 .25 .20 .15 (sum .90)
    # score = (.30*.40909 + .25*.5 + 0 + .15*.63636) / .90 = 38.13
    r = compute(SCENARIO, {}, None)
    assert r["components"] == {"alignment": 0.4091, "required_coverage": 0.5, "evidence": 0.0,
                               "gap_health": 0.6364, "roadmap": None}
    assert r["score"] == 38.13 and r["label"] == "Building foundations"
    assert sum(r["weights"].values()) == pytest.approx(1, abs=1e-3) and "roadmap" not in r["weights"]
    assert r["metrics"]["alignment_pct"] == 40.91 and r["metrics"]["high_priority_open"] == 1



def test_scenario_b_evidence_and_roadmap_raise_score_but_not_classification():
    # E = (2*1.0 + 1*0.6)/5.5 = .472727  P = .5   score = .30*.40909+.25*.5+.20*.472727+.15*.63636+.10*.5 = 48.77
    r = compute(SCENARIO, {"fastapi": 1.0, "docker": 0.6}, 50.0)
    assert r["score"] == 48.77 and r["components"]["evidence"] == 0.4727 and r["components"]["roadmap"] == 0.5
    assert r["components"]["alignment"] == 0.4091                              # alignment is untouched
    assert [b["classification"] for b in r["breakdown"]] == ["strong", "gap", "gap", "partial"]


def test_scenario_c_not_enough_data():
    for reqs in ([], SCENARIO[:2]):
        r = compute(reqs, {}, None)
        assert r["score"] is None and r["label"] == "Not enough data" and r["weights"] == {}


def test_no_required_skills_drops_coverage_and_renormalises():
    reqs = [Req(n, I.preferred, C.partial, P.low) for n in ("A", "B", "C")]
    r = compute(reqs, {}, None)
    assert r["components"]["required_coverage"] is None and "required_coverage" not in r["weights"]
    assert sum(r["weights"].values()) == pytest.approx(1, abs=1e-3)
    assert r["score"] == round(100 * (.30 * .5 + .20 * 0 + .15 * 1) / .65, 2)   # = 46.15


def test_perfect_match_and_empty_match_bounds():
    best = [Req(n, I.required, C.strong, P.none) for n in "ABC"]
    worst = [Req(n, I.required, C.gap, P.high) for n in "ABC"]
    assert compute(best, {"a": 1, "b": 1, "c": 1}, 100)["score"] == 100.0
    assert compute(worst, {}, 0)["score"] == 0.0


def test_evidence_strength_is_clipped_and_deterministic():

    assert compute(SCENARIO, {"fastapi": 9.0}, None) == compute(SCENARIO, {"fastapi": 1.0}, None)
    assert compute(SCENARIO, {}, 20) == compute(SCENARIO, {}, 20)


@pytest.mark.parametrize("score,label", [(None, "Not enough data"), (0, "Getting started"), (29.99, "Getting started"),
                                         (30, "Building foundations"), (50, "Making progress"), (70, "Strong progress"),
                                         (85, "Highly aligned"), (100, "Highly aligned")])
def test_labels(score, label):
    assert label_for(score) == label


# ---------- API ----------
@pytest.fixture()
def rd(api):
    app = FastAPI()
    app.include_router(readiness_router)
    app.dependency_overrides.update(api.app.dependency_overrides)
    c = TestClient(app)
    return SimpleNamespace(c=c, api=api, app=app, calc=lambda aid=None: c.post(f"/readiness/{aid or api.aid}/calculate"),
                           get=lambda aid=None: c.get(f"/readiness/{aid or api.aid}"))


def add_evidence(api, skill, status, kind=EvidenceKind.github_repo, url="https://github.com/vinod/app"):
    with api.Session() as s:
        s.add(ProgressEvidence(user_id=api.uid, skill_name=skill, kind=kind, url=url, verification_status=status))
        s.commit()


def test_seeded_analysis_without_roadmap(rd):
    # Python required strong, FastAPI required transferable(high), Docker required gap(high), Kubernetes optional gap.
    # sum(w)=6.5  A=2.5/6.5  C=1/3  E=0  G=1-4/6.5   score = (.30*.384615+.25*.3333+.15*.384615)/.90 = 28.49
    r = rd.calc()

    d = r.json()
    assert r.status_code == 201 and d["score"] == 28.49 and d["label"] == "Getting started"
    assert d["roadmap_included"] is False and d["components"]["roadmap"] is None and d["is_stale"] is False
    assert d["metrics"]["required_covered"] == 1 and d["metrics"]["high_priority_open"] == 2
    assert {b["skill_name"] for b in d["breakdown"]} == {"Python", "FastAPI", "Docker", "Kubernetes"}
    assert d["formula_version"] == cfg.FORMULA_VERSION and "next_action" in d


def test_roadmap_progress_evidence_then_score_moves_and_staleness(rd):
    first = rd.calc().json()
    rm = create(rd.api)                                   # roadmap with 0% done -> P = 0 enters the formula
    assert rd.get().json()["is_stale"] is True            # a roadmap now exists
    d = rd.calc().json()
    assert d["score"] == 25.64 and d["roadmap_included"] is True and d["id"] == first["id"]   # same-day update, same row
    docker = next(i for i in rm["items"] if i["skill_name"] == "Docker")
    rd.api.client.patch(f"/roadmaps/{rm['id']}/items/{docker['id']}", json={"status": "completed"})
    assert rd.get().json()["is_stale"] is True and rd.get().json()["score"] == 25.64   # stored value is not silently changed
    # Docker done: P=1/2, E=2*.25/6.5.  score = .115385+.083333+.2*.076923+.057692+.1*.5 = 32.18
    assert rd.calc().json()["score"] == 32.18
    add_evidence(rd.api, "Docker", VerificationStatus.verified)          # E = 2*1/6.5 -> 36.79
    assert rd.get().json()["is_stale"] is True
    after = rd.calc().json()
    assert after["score"] == 36.79 and after["is_stale"] is False
    with rd.api.Session() as s:
        assert s.query(ReadinessSnapshot).count() == 1


def test_unrelated_evidence_does_not_make_a_score_stale(rd):
    rd.calc()
    add_evidence(rd.api, "Photoshop", VerificationStatus.verified)
    assert rd.get().json()["is_stale"] is False



def test_evidence_never_changes_module4_results_or_skills(rd):
    def snap():
        with rd.api.Session() as s:
            return ([(r.id, r.classification, r.priority) for r in s.query(SkillGapResult).all()],
                    [(u.skill_name, u.self_assessed_level) for u in s.query(UserSkill).all()])
    before = snap()
    add_evidence(rd.api, "Docker", VerificationStatus.verified)
    rd.calc()
    assert snap() == before


def test_get_before_calculate_is_404_and_foreign_or_missing_analysis_404(rd):
    assert rd.get().status_code == 404
    assert rd.get(9999).status_code == 404 and rd.calc(9999).status_code == 404
    rd.calc()
    rd.api.as_user(rd.api.other)
    assert rd.get().status_code == 404 and rd.calc().status_code == 404
    rd.api.as_user(rd.api.uid)
    assert rd.get().status_code == 200


def test_failed_analysis_is_400(rd):
    with rd.api.Session() as s:
        a = s.get(SkillGapAnalysis, rd.api.aid)
        a.status = AnalysisStatus.failed
        s.commit()
    assert rd.calc().status_code == 400


def test_login_required(rd):
    rd.app.dependency_overrides.pop(get_current_user)

    assert rd.get().status_code in (401, 403) and rd.calc().status_code in (401, 403)