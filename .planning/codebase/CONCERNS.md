# Codebase Concerns

**Analysis Date:** 2026-11-01

## Tech Debt

**Omitted ML Dependencies in requirements.txt:**
- Issue: `sentence-transformers` (v6.1.0) and `torch` (v2.14.0) are actively imported and used by `backend/app/services/embedding_service.py`, but neither package is declared in `backend/requirements.txt`.
- Files: `backend/requirements.txt`, `backend/app/services/embedding_service.py`
- Impact: A clean environment install using `pip install -r requirements.txt` succeeds but runtime execution immediately crashes with `ModuleNotFoundError: No module named 'sentence_transformers'` when semantic skill matching runs.
- Fix approach: Add `sentence-transformers>=6.1.0` and `torch>=2.14.0` to `backend/requirements.txt`.

**Encoding of requirements.txt:**
- Issue: `backend/requirements.txt` is encoded in UTF-16LE rather than UTF-8.
- Files: `backend/requirements.txt`
- Impact: Many standard CLI tools, Docker builds, and automated dependency scanners misinterpret the file as binary or fail to read lines.
- Fix approach: Re-save `backend/requirements.txt` with UTF-8 (without BOM) encoding.

**Rogue File in `__pycache__`:**
- Issue: A stray Python source file `roadmaps.py` is present inside `backend/app/api/routes/__pycache__/`.
- Files: `backend/app/api/routes/__pycache__/roadmaps.py`
- Impact: Clutters git history and confuses IDE code indexers.
- Fix approach: Delete `backend/app/api/routes/__pycache__/roadmaps.py` and ensure `.gitignore` properly covers all `__pycache__` folders.

**Scattered Test Locations:**
- Issue: Unit tests are split across `backend/tests/` and inside the production package `backend/app/services/` (`test_embedding_service.py`, `test_explanation_service.py`, `test_skill_gap_engine.py`, `test_skill_matching_service.py`).
- Files: `backend/app/services/test_*.py`, `backend/tests/`
- Impact: Confusion regarding canonical test commands; test files packaged with production service code.
- Fix approach: Move all test files from `backend/app/services/test_*.py` into `backend/tests/`.

**Deprecated UTC Timestamp Calls:**
- Issue: Extensive use of `datetime.utcnow()` across models and migrations, which is deprecated in Python 3.12+.
- Files: `backend/app/models/roadmap.py`, `backend/app/models/readiness.py`, `backend/app/models/skill.py`, `backend/app/models/job.py`, `backend/app/models/skill_gap.py`
- Impact: Generates dozens of `DeprecationWarning` notices on every test run; scheduled for removal in future Python releases.
- Fix approach: Replace `datetime.utcnow` with `lambda: datetime.now(timezone.utc)`.

## Known Bugs

**Test Suite Execution From Root Workspace:**
- Symptoms: Running `pytest backend/tests` from the workspace root throws `pydantic_core.ValidationError: 10 validation errors for Settings (Field required)`.
- Files: `backend/app/core/config.py`
- Trigger: `SettingsConfigDict(env_file=".env")` resolves `.env` relative to the current working directory, which fails when running tests from outside `backend/`.
- Workaround: Change directory into `backend/` prior to invoking pytest (`cd backend && pytest tests/`).
- Fix approach: Configure `SettingsConfigDict` to resolve `.env` relative to the file location (`Path(__file__).parent.parent.parent / ".env"`) or provide safe default values for test execution.

## Security Considerations

**Plaintext Storage of GitHub Access Tokens:**
- Risk: User GitHub OAuth access tokens are stored in plaintext in the database table `github_connections`.
- Files: `backend/app/models/github_connection.py:18` (`access_token = Column(String(500), nullable=False)`)
- Current mitigation: None at the application level.
- Recommendations: Encrypt tokens at rest using symmetric encryption (e.g. `cryptography.fernet.Fernet`) before saving to the database, decrypting only during active GitHub API calls.

**Frontend Environment Leakage in Browser Console:**
- Risk: `frontend/src/api/axios.js` unconditionally logs all environment variables to the browser console.
- Files: `frontend/src/api/axios.js:3` (`console.log('DEBUG ENV:', import.meta.env);`)
- Current mitigation: None.
- Recommendations: Remove the `console.log` statement before production builds.

## Performance Bottlenecks

**In-Process ML Vector Model Memory Overhead:**
- Problem: `SentenceTransformer("all-MiniLM-L6-v2")` is loaded in memory via PyTorch in the API process.
- Files: `backend/app/services/embedding_service.py`
- Cause: PyTorch model weights and runtime take significant memory (~200MB+ per process).
- Improvement path: In multi-worker production environments, consider offloading embeddings to a dedicated service or utilizing external lightweight embedding APIs.

**Cold Start on Semantic Matching:**
- Problem: The first skill gap analysis request experiences latency due to lazy model loading.
- Files: `backend/app/services/embedding_service.py:31`
- Cause: `_load_model()` runs synchronously on the first `embed()` call.
- Improvement path: Warm up the embedding model during FastAPI startup (`@app.on_event("startup")`).

## Fragile Areas

**Database Schema Migrations:**
- Files: `backend/app/main.py:48`, `backend/migrations/module6.sql`
- Why fragile: `Base.metadata.create_all(bind=engine)` creates missing tables but cannot apply schema updates (e.g. `ALTER TABLE`) to existing tables. Schema alterations must be executed manually via raw SQL scripts.
- Safe modification: Adopt Alembic (`alembic init`) for version-controlled, automated schema migrations.

**Hardcoded Gemini Model Identifiers:**
- Files: `backend/app/services/gemini_service.py:16`, `backend/app/services/roadmap/roadmap_llm.py`
- Why fragile: Model string `gemini-3.6-flash` is hardcoded across service calls. If Google deprecates or changes availability for this model tag, requests fail with HTTP 502.
- Safe modification: Move the model name into `backend/app/core/config.py` as a configurable setting.

## Missing Critical Features

**Automated Frontend Testing:**
- Problem: There are zero automated unit or integration tests for the React frontend.
- Blocks: Regressions in authentication flows, roadmap interactive cards, or skill profile edits cannot be caught automatically in CI.

**Database Migration Tooling:**
- Problem: No formal Alembic integration is configured.
- Blocks: Safe, automated zero-downtime database migrations across development and production environments.

## Test Coverage Gaps

**Frontend UI & Component Tests:**
- What's not tested: All React components, form submissions, ProtectedRoute redirection, and error handling.
- Files: `frontend/src/pages/*.jsx`, `frontend/src/components/**/*.jsx`
- Risk: UI breakages or broken API contract integrations go unnoticed until manual user verification.
- Priority: High

**Integration Tests for External Auth & LLM Flows:**
- What's not tested: Real GitHub OAuth roundtrip and real Google GenAI response verification (tests currently use mock stubs).
- Files: `backend/app/services/github_service.py`, `backend/app/services/gemini_service.py`
- Risk: Breaking changes in third-party API contracts may fail silently until production runtime.
- Priority: Medium

---

*Concerns audit: 2026-11-01*

