"""Module 6 demo-safety fixes: next best action, Gemini feedback safety/timeout, evidence strengths.
Pure unit tests: no database, no network, no Gemini."""
import time
from types import SimpleNamespace as NS

import pytest

from app.core import readiness_config as cfg
from app.models.job import Importance
from app.models.readiness import EvidenceKind, VerificationStatus
from app.models.roadmap import ItemStatus
from app.models.skill_gap import MatchClassification as M, PriorityLevel as P
from app.services import readiness_service as svc
from app.services.evidence_service import strength
from app.services.readiness_engine import Req


def item(i, skill, status=ItemStatus.not_started, priority=P.medium, prereqs=(), scheduled=True):
    return NS(id=i, skill_name=skill, status=status, priority=priority, prerequisites=list(prereqs),
              is_scheduled=scheduled, order_index=i)


def roadmap(*items):
    return NS(id=1, items=list(items))


# ---------- Fix 2 + 3: next best action ----------

def test_prerequisite_already_known_does_not_block():
    # Python is not in the roadmap (user already has it), so FastAPI must be startable.
    rm = roadmap(item(1, "FastAPI", priority=P.high, prereqs=["Python"]))
    act = svc.select_next_action([], {}, rm)
    assert act.kind == "roadmap_item" and act.skill_name == "FastAPI"


def test_prerequisite_in_roadmap_blocks_until_done():
    rm = roadmap(item(1, "Docker", priority=P.medium), item(2, "Kubernetes", priority=P.high, prereqs=["Docker"]))
    assert svc.select_next_action([], {}, rm).skill_name == "Docker"
    rm.items[0].status = ItemStatus.completed
    assert svc.select_next_action([], {}, rm).skill_name == "Kubernetes"


def test_in_progress_comes_first():
    rm = roadmap(item(1, "SQL", priority=P.high), item(2, "Git", status=ItemStatus.in_progress, priority=P.low))
    act = svc.select_next_action([], {}, rm)
    assert act.skill_name == "Git" and "in_progress" in act.reason_codes


def test_reason_code_uses_plain_value():
    rm = roadmap(item(1, "Docker", priority=P.high))
    codes = svc.select_next_action([], {}, rm).reason_codes
    assert "priority_high" in codes
    assert not any("PriorityLevel" in c for c in codes)


def test_evidence_action_prefers_required_skill():
    reqs = [Req("AWS", Importance.preferred, M.gap, P.high), Req("Docker", Importance.required, M.gap, P.high)]
    act = svc.select_next_action(reqs, {}, None)
    assert act.kind == "add_evidence" and act.skill_name == "Docker"


def test_rerun_when_evidence_present():
    reqs = [Req("Docker", Importance.required, M.partial, P.high)]
    assert svc.select_next_action(reqs, {"docker": 1.0}, None).kind == "rerun_analysis"


# ---------- Fix 4: Gemini feedback safety, timeout, fallback ----------

@pytest.mark.parametrize("bad", [
    "Great work! You will get hired soon if you keep this pace up.",
    "Your chances of landing a role are now 80% based on this score.",
    "You are definitely job-ready now, well done on all your progress.",
    "Read more at https://example.com to keep improving your skills.",
    "short",
])
def test_bad_feedback_rejected(bad):
    assert svc._clean_feedback(bad) is None


def test_good_feedback_accepted():
    text = "You have covered two of three required skills. Finishing the Docker milestone is the best next step."
    assert svc._clean_feedback(text) == text


def _act():
    return svc.NextAction(kind="roadmap_item", title="Start learning Docker")


def test_feedback_falls_back_on_error(monkeypatch):
    monkeypatch.setattr(svc, "_gemini_feedback_call", lambda p: (_ for _ in ()).throw(RuntimeError("down")))
    out = svc._generate_ai_feedback(55.0, "Making progress", {"required_covered": 2, "required_total": 3}, _act())
    assert "55.0/100" in out and "Start learning Docker" in out


def test_feedback_falls_back_on_banned_text(monkeypatch):
    monkeypatch.setattr(svc, "_gemini_feedback_call", lambda p: "Keep going and you will be hired within a month for sure.")
    out = svc._generate_ai_feedback(55.0, "Making progress", {}, _act())
    assert "hired" not in out and "55.0/100" in out


def test_feedback_timeout_returns_fast(monkeypatch):
    monkeypatch.setattr(cfg, "FEEDBACK_TIMEOUT_SECONDS", 0.3)
    monkeypatch.setattr(svc, "_gemini_feedback_call", lambda p: (time.sleep(2), "late text that is long enough")[1])
    t0 = time.monotonic()
    out = svc._generate_ai_feedback(55.0, "Making progress", {}, _act())
    assert time.monotonic() - t0 < 1.5
    assert "55.0/100" in out


def test_prompt_contains_no_personal_data(monkeypatch):
    seen = {}
    monkeypatch.setattr(svc, "_gemini_feedback_call", lambda p: seen.setdefault("p", p) and None)
    svc._generate_ai_feedback(55.0, "Making progress", {}, _act())
    assert "http" not in seen["p"] and "@" not in seen["p"]


# ---------- Fix 5: evidence strengths ----------

def test_project_link_below_unchecked_repo():
    link = strength(EvidenceKind.project_url, VerificationStatus.linked)
    assert link == 0.40
    assert cfg.LEARNING_STRENGTH < link < strength(EvidenceKind.github_repo, VerificationStatus.linked)
    assert strength(EvidenceKind.github_repo, VerificationStatus.verified) == 1.0


def test_formula_version_bumped():
    assert cfg.FORMULA_VERSION == "1.1"   # old snapshots show as stale and get recalculated


# ---------- Fix 1: snapshot whose analysis was deleted ----------

def _snap(**kw):
    base = dict(id=7, job_description_id=3, analysis_id=None, roadmap_id=None, score=42.0, label="Building foundations",
                roadmap_included=False, a_alignment=0.5, c_required_coverage=0.3, e_evidence=0.2, g_gap_health=0.6,
                p_roadmap=None, metrics={}, formula_version="1.1", trigger="manual", next_action=None,
                ai_feedback="x", snapshot_date=None, created_at=None, input_fingerprint="abc")
    base.update(kw)
    return NS(**base)


def test_deleted_analysis_still_returns_stored_score():
    out = svc.to_response(db=None, user_id=1, snap=_snap())
    assert out["score"] == 42.0 and out["source_available"] is False and out["is_stale"] is False
    assert out["breakdown"] == []


def test_stored_weights_renormalise_without_roadmap():
    w = svc._stored_weights(_snap())
    assert set(w) == {"alignment", "required_coverage", "evidence", "gap_health"}
    assert abs(sum(w.values()) - 1.0) < 1e-3 and w["alignment"] == round(0.30 / 0.90, 4)


def test_missing_analysis_handled(monkeypatch):
    def boom(*a, **k):
        raise svc.HTTPException(404, "Analysis not found")
    monkeypatch.setattr(svc, "_run", boom)
    out = svc.to_response(db=None, user_id=1, snap=_snap(analysis_id=99))
    assert out["source_available"] is False and out["score"] == 42.0


# ---------- Fix 7: one alignment number everywhere ----------

def test_comparison_alignment_matches_engine():
    from app.services import readiness_engine as engine
    rows = [(Importance.required, M.strong), (Importance.required, M.partial), (Importance.preferred, M.gap),
            (Importance.optional, M.transferable)]
    results = [NS(job_requirement=NS(importance=i, skill_name=f"s{n}"), classification=c) for n, (i, c) in enumerate(rows)]
    reqs = [Req(f"s{n}", i, c, P.none) for n, (i, c) in enumerate(rows)]
    assert svc._alignment_pct(results) == engine.compute(reqs, {}, None)["metrics"]["alignment_pct"]
