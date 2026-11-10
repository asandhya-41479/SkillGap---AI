# External Integrations

**Analysis Date:** 2026-11-01

## APIs & External Services

**AI & Large Language Models:**
- Google Gemini API (`backend/app/services/gemini_service.py`, `backend/app/services/roadmap/roadmap_llm.py`, `backend/app/services/explanation_service.py`)
  - Used for:
    - Extracting structured technical skills and requirements from unstructured job descriptions
    - Generating personalized learning topics, practical exercises, and project milestones for roadmap items
    - Synthesizing natural language explanations for skill gaps and career readiness scores
  - Models called: `gemini-3.6-flash` (with fallback handling for unavailable or malformed responses)
  - SDK/Client: `google-genai` (`genai.Client`)
  - Auth: `GEMINI_API_KEY` environment variable (`backend/app/core/config.py`)

**Version Control & Developer Identity:**
- GitHub REST API (`backend/app/services/github_service.py`, `backend/app/services/github_evidence.py`, `backend/app/api/routes/github.py`)
  - Used for:
    - OAuth 2.0 user authorization and profile linkage
    - Querying user repositories, repository ownership, languages, and repo topics
    - Verifying structural repository signals (file checks, config files) for skill evidence verification
  - SDK/Client: HTTP clients (`httpx`, `requests`) calling `https://api.github.com`
  - Auth: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`, `GITHUB_FRONTEND_REDIRECT` in backend configuration; user-level access tokens stored in `github_connections` table

**Local Machine Learning Services:**
- Local Sentence Transformers (`backend/app/services/embedding_service.py`)
  - Model: `all-MiniLM-L6-v2` loaded in-memory via PyTorch
  - Used for: Semantic skill matching (computing cosine similarities between user skills and job requirements when exact string match fails)

## Data Storage

**Databases:**
- PostgreSQL (Direct or Supabase hosted)
  - Connection: `DATABASE_URL` environment variable
  - Client: `SQLAlchemy` 2.0 ORM with `psycopg2-binary` engine (`backend/app/db/database.py`)
  - Schema Management: Initial table bootstrap via `Base.metadata.create_all(bind=engine)` in `backend/app/main.py`, incremental alterations via SQL scripts in `backend/migrations/` (e.g. `backend/migrations/module6.sql`)
  - Primary Tables:
    - `users`: Core user accounts and target career roles
    - `user_skills`, `skill_evidence`: Declared skills and detected repository evidence
    - `github_connections`, `oauth_states`: Connected GitHub accounts and CSRF state tracking
    - `job_descriptions`, `job_requirements`: Parsed job targets and extracted requirements
    - `skill_gap_analyses`, `skill_gap_results`: Evaluated gaps, classifications, and priorities
    - `roadmaps`, `roadmap_items`: Multi-week structured learning plans
    - `progress_evidence`, `readiness_snapshots`: Career readiness metrics and evidence items

**File Storage:**
- Local filesystem / In-memory: Resume uploads (`.pdf`, `.docx`) are parsed in-memory using `PyMuPDF` and `python-docx` without persistent object store storage.

**Caching:**
- In-process memory: `@lru_cache(maxsize=2048)` applied to `EmbeddingService._embed_cached` (`backend/app/services/embedding_service.py`). No external Redis or Memcached instance.

## Authentication & Identity

**Auth Provider:**
- Custom JWT (JSON Web Token) implementation (`backend/app/core/security.py`, `backend/app/dependencies/auth.py`, `backend/app/api/routes/auth.py`)
  - Implementation: Passwords hashed using bcrypt via `passlib.context.CryptContext`. Access tokens signed using HMAC with secret key (`SECRET_KEY`) and algorithm (`ALGORITHM`, e.g. `HS256`).
  - Expiration: Managed via `ACCESS_TOKEN_EXPIRE_MINUTES`.
  - Client storage: Stored in browser `localStorage` under `access_token` and passed via HTTP `Authorization: Bearer <token>` header (`frontend/src/api/axios.js`).

**Third-Party OAuth:**
- GitHub OAuth 2.0 (`backend/app/api/routes/github.py`):
  - Flow: User initiates at `/github/login`, redirected to GitHub with CSRF state token stored in `oauth_states`, redirected back to `/github/callback`, exchanged for user access token and persisted in `github_connections`.

## Monitoring & Observability

**Error Tracking:**
- None configured (no Sentry, Rollbar, or Bugsnag integration).

**Logs:**
- Standard Python `logging` module (`logging.getLogger(__name__)`) configured in service modules (`backend/app/services/embedding_service.py`, `backend/app/services/readiness_service.py`, etc.).
- Frontend console debugging in `frontend/src/api/axios.js`.

**Health Monitoring:**
- `GET /health` endpoint defined in `backend/app/main.py` returning `{"status": "ok"}`.

## CI/CD & Deployment

**Hosting:**
- Not defined in repository (no Dockerfile, docker-compose.yml, or deployment manifests found).

**CI Pipeline:**
- None configured (no `.github/workflows` directory present).

## Environment Configuration

**Required Environment Variables (Backend `.env`):**
- `DATABASE_URL`: PostgreSQL connection URL (e.g. `postgresql://user:pass@host:5432/db`)
- `SECRET_KEY`: Random string for JWT signature generation
- `ALGORITHM`: Token algorithm (typically `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT token lifetime in minutes
- `FRONTEND_ORIGIN`: Allowed origin for CORS middleware (e.g. `http://localhost:5173`)
- `GITHUB_CLIENT_ID`: GitHub OAuth app client ID
- `GITHUB_CLIENT_SECRET`: GitHub OAuth app secret
- `GITHUB_REDIRECT_URI`: Backend callback URL (`http://localhost:8000/github/callback`)
- `GITHUB_FRONTEND_REDIRECT`: Frontend post-auth landing URL (`http://localhost:5173/skills`)
- `GEMINI_API_KEY`: API key for Google Gemini GenAI services

**Secrets Location:**
- Local uncommitted `.env` file in `backend/.env`.
- Frontend environment variable `VITE_API_URL` injected at build/runtime.

## Webhooks & Callbacks

**Incoming:**
- `GET /github/callback` (`backend/app/api/routes/github.py`) - Receives GitHub OAuth `code` and `state` parameters from user authorization redirect.

**Outgoing:**
- None (system does not push webhooks to external services).

---

*Integration audit: 2026-11-01*

