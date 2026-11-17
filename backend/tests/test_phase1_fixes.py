"""Phase 1 tests: "X, Y or Z" alternatives (1A) and the GitHub callback always returning to the app (1B)."""
import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.job import Importance
from app.models.skill_gap import MatchClassification, PriorityLevel
from app.services.embedding_service import embedding_service
from app.services.requirement_processor import process_extraction
from app.services.skill_gap_engine import run_gap_analysis

JD = ("Required: Python, Vector Databases (Pinecone, FAISS or Chroma). "
      "Preferred: AWS or GCP, Docker.")


def skill(name, category="programming_language", skill_id=1):
    return SimpleNamespace(id=skill_id, skill_name=name, category=SimpleNamespace(value=category))


def req(name, importance=Importance.required, alternatives=None, category="database", req_id=1):
    return SimpleNamespace(id=req_id, skill_name=name, category=SimpleNamespace(value=category),
                           importance=importance, alternatives=alternatives)


@pytest.fixture
def no_similarity(monkeypatch):
    """Non-exact names never look similar, so only exact (normalized) matches count."""
    monkeypatch.setattr(embedding_service, "cosine_similarity", lambda a, b: 0.0)


# ---------------------------------------------------------------- 1A: extraction

def test_alternatives_kept_when_written_in_the_text():
    out = process_extraction([{"name": "Vector Databases", "category": "database", "importance": "required",
                               "alternatives": ["Pinecone", "FAISS", "Chroma"]}], JD)
    assert len(out) == 1
    assert [a.lower() for a in out[0]["alternatives"]] == ["pinecone", "faiss", "chroma"]


def test_invented_alternative_is_rejected():
    out = process_extraction([{"name": "Vector Databases", "category": "database", "importance": "required",
                               "alternatives": ["Pinecone", "Weaviate"]}], JD)   # Weaviate is not in the JD
    assert [a.lower() for a in out[0]["alternatives"]] == ["pinecone"]


def test_no_job_text_means_no_alternatives():
    out = process_extraction([{"name": "Vector Databases", "category": "database", "importance": "required",
                               "alternatives": ["Pinecone"]}])
    assert out[0]["alternatives"] == []


def test_option_also_listed_separately_is_folded_into_the_group():
    raw = [
        {"name": "Vector Databases", "category": "database", "importance": "preferred",
         "alternatives": ["Pinecone", "FAISS", "Chroma"]},
        {"name": "FAISS", "category": "database", "importance": "required"},
        {"name": "Python", "category": "programming_language", "importance": "required"},
    ]
    out = {i["skill_name"].lower(): i for i in process_extraction(raw, JD)}
    assert set(out) == {"vector databases", "python"}               # FAISS is not a separate requirement
    assert out["vector databases"]["importance"] == "required"     # the stronger importance is kept


def test_malformed_alternatives_are_ignored():
    out = process_extraction([{"name": "Docker", "category": "devops", "importance": "preferred",
                               "alternatives": "AWS"}], JD)
    assert out[0]["alternatives"] == []


def test_items_without_alternatives_are_unchanged():
    out = process_extraction([{"name": "Python", "category": "programming_language", "importance": "required"}], JD)
    assert out == [{"skill_name": out[0]["skill_name"], "category": "programming_language",
                    "importance": "required", "alternatives": []}]


# ---------------------------------------------------------------- 1A: gap analysis

def test_any_one_alternative_satisfies_the_requirement(no_similarity):
    job = SimpleNamespace(requirements=[req("Vector Databases", alternatives=["Pinecone", "FAISS", "Chroma"])])
    results, score = run_gap_analysis(job, [skill("FAISS", "database")])
    assert results[0].match.classification == MatchClassification.strong
    assert results[0].priority == PriorityLevel.none
    assert score == 100.0


def test_no_alternative_matched_is_one_gap_not_three(no_similarity):
    job = SimpleNamespace(requirements=[req("Vector Databases", alternatives=["Pinecone", "FAISS", "Chroma"])])
    results, score = run_gap_analysis(job, [skill("Python")])
    assert len(results) == 1
    assert results[0].match.classification == MatchClassification.gap
    assert results[0].priority == PriorityLevel.high
    assert score == 0.0


def test_grouping_raises_the_score_fairly(no_similarity):
    """Python known; vector DB missing. Grouped = 1 gap; ungrouped (old behaviour) = 4 gaps."""
    user = [skill("Python")]
    grouped = SimpleNamespace(requirements=[
        req("Python", category="programming_language", req_id=1),
        req("Vector Databases", alternatives=["Pinecone", "FAISS", "Chroma"], req_id=2),
    ])
    ungrouped = SimpleNamespace(requirements=[
        req("Python", category="programming_language", req_id=1),
        req("Vector Databases", req_id=2), req("Pinecone", req_id=3), req("FAISS", req_id=4), req("Chroma", req_id=5),
    ])
    assert run_gap_analysis(grouped, user)[1] == 50.0
    assert run_gap_analysis(ungrouped, user)[1] == 20.0


def test_old_requirements_without_alternatives_behave_as_before(no_similarity):
    old_style = SimpleNamespace(id=1, skill_name="Python", category=SimpleNamespace(value="programming_language"),
                                importance=Importance.required)       # no "alternatives" attribute at all
    results, score = run_gap_analysis(SimpleNamespace(requirements=[old_style]), [skill("Python")])
    assert results[0].match.classification == MatchClassification.strong
    assert score == 100.0


# ---------------------------------------------------------------- 1B: GitHub callback

@pytest.fixture
def github_route(monkeypatch):
    from app.api.routes import github as route
    monkeypatch.setattr(route.settings, "github_frontend_redirect", "https://app.example/skills")
    return route


def _location(response):
    return response.headers["location"]


def test_callback_success_returns_to_app_with_connected(github_route, monkeypatch):
    svc = github_route.github_service
    saved = {}

    async def token(code):
        return "tok"

    async def profile(t):
        return {"login": "someone", "id": 7}

    monkeypatch.setattr(svc, "validate_and_consume_state", lambda db, s: 42)
    monkeypatch.setattr(svc, "exchange_code_for_token", token)
    monkeypatch.setattr(svc, "fetch_github_profile", profile)
    monkeypatch.setattr(svc, "upsert_github_connection", lambda db, **kw: saved.update(kw))

    r = asyncio.run(github_route.github_callback(code="c", state="s", db=None))
    assert _location(r) == "https://app.example/skills?github=connected"
    assert saved["user_id"] == 42 and saved["github_username"] == "someone"


def test_callback_failure_returns_to_app_not_raw_json(github_route, monkeypatch):
    def bad_state(db, s):
        raise HTTPException(400, "Invalid OAuth state.")

    monkeypatch.setattr(github_route.github_service, "validate_and_consume_state", bad_state)
    r = asyncio.run(github_route.github_callback(code="c", state="s", db=None))
    assert _location(r) == "https://app.example/skills?github=error"


def test_callback_cancelled_on_github_returns_to_app(github_route):
    r = asyncio.run(github_route.github_callback(code=None, state="s", db=None))
    assert _location(r) == "https://app.example/skills?github=error"
    assert "Invalid" not in _location(r)          # no internal reason leaks into the URL
