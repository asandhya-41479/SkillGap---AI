from types import SimpleNamespace

import pytest

from app.models.job import Importance
from app.models.skill_gap import ExplanationSource, MatchClassification, MatchMethod, PriorityLevel
from app.core.skill_gap_config import PRIORITY_TABLE
from app.services import explanation_service
from app.services.embedding_service import EmbeddingServiceUnavailable, embedding_service
from app.services.skill_gap_engine import GapEngineResult, run_gap_analysis
from app.services.skill_matching_service import MatchCandidate, classify_similarity, find_best_match


def skill(name, category="programming_language", skill_id=1):
    return SimpleNamespace(id=skill_id, skill_name=name, category=SimpleNamespace(value=category))


def requirement(name, category="programming_language", importance=Importance.required, req_id=1):
    return SimpleNamespace(
        id=req_id, skill_name=name, category=SimpleNamespace(value=category), importance=importance
    )


def stub_similarity(monkeypatch, score):
    monkeypatch.setattr(embedding_service, "cosine_similarity", lambda a, b: score)


# ---- classify_similarity (pure logic) ----

@pytest.mark.parametrize(
    "score, same_cat, eco, expected",
    [
        (0.98, True, False, MatchClassification.strong),
        (0.80, True, False, MatchClassification.strong),        # boundary
        (0.61, True, False, MatchClassification.partial),
        (0.45, True, False, MatchClassification.partial),       # boundary
        (0.61, False, False, MatchClassification.transferable),
        (0.19, True, False, MatchClassification.partial),       # category floor
        (0.10, True, False, MatchClassification.gap),           # below floor
        (0.12, False, True, MatchClassification.transferable),  # ecosystem pair
        (0.12, False, False, MatchClassification.gap),
    ],
)
def test_classify_similarity(score, same_cat, eco, expected):
    assert classify_similarity(score, same_cat, eco) == expected


# ---- find_best_match ----

def test_exact_match_normalizes_react_js():
    result = find_best_match("React.js", "framework", [skill("React", "framework")])
    assert result.classification == MatchClassification.strong
    assert result.match_method == MatchMethod.exact
    assert result.similarity_score == 1.0


def test_duplicate_user_skills_still_strong():
    result = find_best_match("Python", "programming_language", [skill("Python", skill_id=1), skill("Python", skill_id=2)])
    assert result.classification == MatchClassification.strong


def test_no_user_skills_is_gap():
    result = find_best_match("Docker", "devops", [])
    assert result.classification == MatchClassification.gap
    assert result.match_method == MatchMethod.none
    assert result.matched_user_skill is None


def test_semantic_partial(monkeypatch):
    stub_similarity(monkeypatch, 0.61)
    result = find_best_match("SQL databases", "database", [skill("PostgreSQL", "database")])
    assert result.classification == MatchClassification.partial
    assert result.match_method == MatchMethod.semantic


def test_ecosystem_transferable(monkeypatch):
    stub_similarity(monkeypatch, 0.1241)
    result = find_best_match("FastAPI", "framework", [skill("Python")])
    assert result.classification == MatchClassification.transferable
    assert result.matched_user_skill.skill_name == "Python"


def test_unrelated_is_gap_and_matched_skill_cleared(monkeypatch):
    stub_similarity(monkeypatch, 0.05)
    result = find_best_match("Docker", "devops", [skill("Python")])
    assert result.classification == MatchClassification.gap
    assert result.matched_user_skill is None


def test_false_friend_java_vs_javascript_is_gap():
    result = find_best_match("JavaScript", "programming_language", [skill("Java")])
    assert result.classification == MatchClassification.gap


def test_embedding_failure_fails_safe(monkeypatch):
    def boom(a, b):
        raise EmbeddingServiceUnavailable("model missing")

    monkeypatch.setattr(embedding_service, "cosine_similarity", boom)
    result = find_best_match("FastAPI", "framework", [skill("Flask", "framework")])
    assert result.classification == MatchClassification.gap
    assert result.match_method == MatchMethod.none


# ---- run_gap_analysis (priority + alignment score) ----

def test_no_requirements_returns_none_score():
    job = SimpleNamespace(requirements=[])
    results, score = run_gap_analysis(job, [skill("Python")])
    assert results == [] and score is None


def test_alignment_score_and_priority(monkeypatch):
    stub_similarity(monkeypatch, 0.0)
    job = SimpleNamespace(requirements=[
        requirement("Python", req_id=1),
        requirement("Docker", "devops", Importance.required, req_id=2),
    ])
    results, score = run_gap_analysis(job, [skill("Python")])
    assert score == 50.0  # (2*1.0 + 2*0.0) / 4
    by_name = {r.job_requirement.skill_name: r for r in results}
    assert by_name["Python"].priority == PriorityLevel.none
    assert by_name["Docker"].priority == PriorityLevel.high


def test_priority_table_required_gap_outranks_preferred_gap():
    assert PRIORITY_TABLE[(Importance.required, MatchClassification.gap)] == PriorityLevel.high
    assert PRIORITY_TABLE[(Importance.preferred, MatchClassification.gap)] == PriorityLevel.medium


# ---- explanations ----

def fake_engine_result(classification, matched_name):
    match = MatchCandidate(
        matched_user_skill=SimpleNamespace(skill_name=matched_name) if matched_name else None,
        similarity_score=0.5,
        classification=classification,
        match_method=MatchMethod.semantic,
    )
    req = SimpleNamespace(skill_name="FastAPI", importance=Importance.required)
    return GapEngineResult(job_requirement=req, match=match, priority=None)


def test_deterministic_explanations_name_the_skills():
    text = explanation_service._deterministic_explanation(fake_engine_result(MatchClassification.transferable, "Python"))
    assert "Python" in text and "FastAPI" in text


def test_gemini_failure_falls_back_to_deterministic(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("503 UNAVAILABLE")

    monkeypatch.setattr(
        explanation_service, "_client", SimpleNamespace(models=SimpleNamespace(generate_content=boom))
    )
    text, source = explanation_service.generate_explanation(fake_engine_result(MatchClassification.gap, None))
    assert source == ExplanationSource.deterministic
    assert "FastAPI" in text