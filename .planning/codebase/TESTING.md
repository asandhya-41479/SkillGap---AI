# Testing Patterns

**Analysis Date:** 2026-11-01

## Test Framework

**Runner:**
- `pytest` (installed in `backend/.venv`)
- Config: Default configuration (no custom `pytest.ini` or `setup.cfg` file present)

**Assertion Library:**
- Standard Python `assert` statements with expressive error messages

**Run Commands:**
```bash
# Run all backend tests (must be run from backend directory to resolve .env)
cd backend && .venv/Scripts/pytest tests/

# Run a specific test suite
cd backend && .venv/Scripts/pytest tests/test_roadmap_rule_engine.py

# Run with verbose output and short summary
cd backend && .venv/Scripts/pytest tests/ -v -q

# Run specific test function
cd backend && .venv/Scripts/pytest tests/test_evidence.py -k "test_verified_repo"
```

*Note on Frontend:* No frontend test runner (e.g. Vitest, Jest, Cypress, Playwright) is currently configured in `frontend/package.json`.

## Test File Organization

**Location:**
- Dedicated test directory: `backend/tests/`
- Stray unit test modules: `backend/app/services/test_embedding_service.py`, `backend/app/services/test_skill_gap_engine.py`

**Naming:**
- Prefix convention: `test_<feature_name>.py`
- Manual diagnostic scripts: `manual_gemini_roadmap.py`, `manual_store_roadmap.py`, `check_models.py`

## Test Structure

**In-Memory SQLite Database Pattern:**
The test suite avoids connecting to live PostgreSQL databases by creating an in-memory SQLite engine with foreign key enforcement enabled:

```python
@pytest.fixture()
def api(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    event.listen(engine, "connect", lambda c, _: c.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    with Session() as s:
        u, other, a = seed(s)
        ids = (u.id, other.id, a.id)

    # Dependency override session generator
    def session():
        with Session() as s:
            yield s

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = session
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=ids[0])
    
    return SimpleNamespace(
        client=TestClient(app),
        app=app,
        Session=Session,
        uid=ids[0],
        aid=ids[2]
    )
```

## Mocking

**Framework:**
- Standard pytest `monkeypatch` fixture

**External Service Mocking Patterns:**

*Mocking Google Gemini LLM:*
```python
class Fake:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def __call__(self, prompt, **kwargs):
        self.calls.append(prompt)
        return self.reply

monkeypatch.setattr(roadmap_llm, "_gemini_call", Fake(good_reply))
```

*Mocking GitHub REST API:*
```python
class FakeGitHub:
    def __init__(self):
        self.repos, self.down, self.calls = {}, False, []

    def __call__(self, path, token, raw=False):
        self.calls.append(path)
        if self.down:
            raise ge.GitHubUnavailable("down")
        # Return faked repository metadata or files
        return 200, {"full_name": "user/repo", "owner": {"login": "user"}}

monkeypatch.setattr(github_evidence, "_get", FakeGitHub())
```

**What to Mock:**
- Network I/O and external third-party APIs (Google Gemini API, GitHub REST API)
- Authentication credentials and JWT decoding in API tests

**What NOT to Mock:**
- Deterministic calculation logic (DAG topological sorter in `planner.py`, effort hours in `effort.py`)
- Career readiness scoring formulas in `readiness_engine.py`
- Relational constraints and schema foreign keys (tested using real SQLite)

## Fixtures and Factories

**Test Data Seeding:**
- Standard seeding helpers (e.g. `seed(session)` in `tests/test_roadmap_rule_engine.py`) populate initial test data:
  - User record (`User(name="Test", email="test@example.com", ...)`)
  - Target job requirements (`JobRequirement(skill_name="Docker", ...)`)
  - Skill gap analysis (`SkillGapAnalysis`, `SkillGapResult`)

## Coverage & Gaps

**Backend Unit Test Coverage:**
- High coverage of deterministic core:
  - `test_roadmap_rule_engine.py`: 194 passing test cases verifying capacity limits, prerequisite ordering, supplementary items, and edge cases.
  - `test_readiness_engine.py`: Verifies mathematical formula weights, component boundaries, and label assignments.
  - `test_evidence.py`: Verifies structural GitHub signal checks and evidence attachment.
  - `test_roadmap_api.py`: Validates FastAPI endpoints, input schemas, and responses.

**Identified Coverage Gaps:**
1. **Frontend Testing:** Zero automated tests in `frontend/`. No unit tests for components or end-to-end user flows.
2. **Root Test Execution:** Pytest cannot be run from root `skillgap ai/` without setting `PYTHONPATH=backend` and having a root `.env` due to Pydantic settings loading behavior.
3. **Deprecation Warnings:** Tests emit `utcnow()` deprecation warnings from SQLAlchemy datetime default handlers.

---

*Testing analysis: 2026-11-01*

