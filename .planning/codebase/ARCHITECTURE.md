<!-- refreshed: 2026-11-01 -->
# Architecture

**Analysis Date:** 2026-11-01

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer (React 19 SPA)            │
├──────────────────┬──────────────────┬───────────────────────┤
│    Auth / Context│    Pages & Views │    Axios API Client   │
│ `frontend/src/`  │ `frontend/src/`  │ `frontend/src/api/`   │
│  AuthContext.jsx │  pages/*.jsx     │  axios.js, *.js       │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI REST API Layer                      │
│ `backend/app/main.py` & `backend/app/api/routes/`           │
│  auth.py, users.py, skills.py, github.py, jobs.py,          │
│  skill_gap.py, roadmaps.py, evidence.py, readiness.py       │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
┌────────────────────────────────┐ ┌──────────────────────────┐
│   Business Logic & Services    │ │  AI & Analysis Engines   │
│ `backend/app/services/`        │ │ `backend/app/services/`  │
│  user_service.py               │ │  skill_gap_engine.py     │
│  skill_service.py              │ │  skill_matching_service  │
│  github_service.py             │ │  embedding_service.py    │
│  job_service.py                │ │  readiness_engine.py     │
│  evidence_service.py           │ │  roadmap/planner.py      │
│  roadmap/roadmap_service.py    │ │  roadmap/roadmap_llm.py  │
└────────────────┬───────────────┘ └───────────┬──────────────┘
                 │                             │
                 ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 Data & External Integrations                │
├────────────────────────────────┬────────────────────────────┤
│  PostgreSQL / SQLAlchemy 2.0   │ Google Gemini API &        │
│ `backend/app/models/`          │ GitHub REST API            │
│ `backend/app/db/database.py`   │ `gemini-3.6-flash` / OAuth │
└────────────────────────────────┴────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| App Entry Point | Configures FastAPI app, CORS middleware, route registration, DB init | `backend/app/main.py` |
| Route Handlers | HTTP endpoint definitions, dependency injection, and schema serialization | `backend/app/api/routes/*.py` |
| Security & Auth | JWT encoding/decoding, password hashing with bcrypt, auth middleware | `backend/app/core/security.py`, `backend/app/dependencies/auth.py` |
| Configuration | Typed environment settings with pydantic-settings | `backend/app/core/config.py` |
| Rule Engines Config | Deterministic weights, effort sizes, skill dependencies, readiness formulas | `backend/app/core/roadmap_config.py`, `backend/app/core/readiness_config.py` |
| Database Session | SQLAlchemy engine, session maker, base declarative metadata | `backend/app/db/database.py`, `backend/app/db/base.py` |
| ORM Entities | Database schemas for users, skills, jobs, gaps, roadmaps, evidence, readiness | `backend/app/models/*.py` |
| Pydantic Schemas | Request validation and response shape contracts | `backend/app/schemas/*.py` |
| Gemini Service | Google GenAI SDK client for requirement extraction | `backend/app/services/gemini_service.py` |
| Embedding Service | In-memory SentenceTransformer (`all-MiniLM-L6-v2`) semantic vector generator | `backend/app/services/embedding_service.py` |
| Skill Gap Engine | Multi-pass exact and semantic skill matching, classification, prioritization | `backend/app/services/skill_gap_engine.py`, `backend/app/services/skill_matching_service.py` |
| Roadmap Planner | Deterministic DAG topological sorting, effort sizing, time capacity budgeter | `backend/app/services/roadmap/planner.py`, `dependency_graph.py`, `effort.py` |
| Roadmap LLM | Gemini roadmap enrichment with deterministic template repair fallback | `backend/app/services/roadmap/roadmap_llm.py` |
| Readiness Engine | Deterministic 5-component weighted career readiness calculation | `backend/app/services/readiness_engine.py`, `backend/app/services/readiness_service.py` |
| GitHub Verifier | Structural checks on repositories to verify skill claims | `backend/app/services/github_evidence.py` |
| Frontend Shell | Root React application with route map and protected routes | `frontend/src/App.jsx`, `frontend/src/main.jsx` |
| Auth Context | Global user session state, login/logout, JWT persistence | `frontend/src/context/AuthContext.jsx` |
| API Layer | Axios instance configured with JWT bearer interceptor | `frontend/src/api/axios.js`, `frontend/src/api/*.js` |

## Pattern Overview

**Overall:** Layered Architecture (Controller-Service-Model) on the backend; Component-driven Single Page Application (SPA) on the frontend.

**Key Characteristics:**
- **Deterministic-First AI Architecture:** Core business decisions (skill gap classification, DAG prerequisite scheduling, effort hours calculation, readiness scoring) are calculated by deterministic Python rule engines. External LLMs (Gemini) are used strictly for qualitative enrichment (topic explanations, study task suggestions) and feature full deterministic fallbacks (`rules_only` / `partial_fallback`).
- **Synchronous Endpoint Execution in Threadpool:** Route handlers in `backend/app/api/routes/` are declared with standard `def` rather than `async def`, allowing FastAPI to dispatch blocking DB and ML calculations (e.g. PyTorch embeddings, SQLAlchemy queries) to anyio worker threads without blocking the main event loop.
- **Traceable Versioning:** Roadmaps preserve `parent_roadmap_id` and `input_snapshot` to maintain full lineage and allow detecting when underlying requirements have shifted.

## Layers

**API Presentation Layer:**
- Purpose: Accepts HTTP requests, parses headers/parameters, authenticates user via JWT, delegates to services, returns serialized JSON.
- Location: `backend/app/api/routes/`
- Contains: FastAPI router declarations (`auth.py`, `jobs.py`, `roadmaps.py`, `skills.py`, etc.)
- Depends on: `backend/app/dependencies/`, `backend/app/schemas/`, `backend/app/services/`
- Used by: Frontend HTTP clients (`frontend/src/api/*.js`)

**Service & Domain Engine Layer:**
- Purpose: Encapsulates all domain computation, business rules, ML inferences, external API integrations, and database transactions.
- Location: `backend/app/services/`
- Contains: Pure Python services, DAG planners, rule engines, embedding caches, and LLM integrations.
- Depends on: `backend/app/models/`, `backend/app/core/`, external libraries (`google.genai`, `sentence_transformers`, `sqlalchemy`)
- Used by: Route handlers in `backend/app/api/routes/`

**Data Persistence Layer:**
- Purpose: Represents relational database tables and handles database connection sessions.
- Location: `backend/app/db/`, `backend/app/models/`
- Contains: `Base` class, SQLAlchemy ORM models with mapped columns, relationships, constraints, and enums.
- Depends on: PostgreSQL / SQLite engine
- Used by: Service layer and route dependencies (`get_db`)

## Data Flow

### Primary Request Path (Skill Gap Analysis to Roadmap Generation)

1. **Job Intake:**
   - Client sends raw job description to `POST /jobs` (`backend/app/api/routes/jobs.py`).
   - `job_service.create_job_description` stores `JobDescription` with status `pending`.
   - `gemini_service.extract_requirements` prompts Gemini 3.6 Flash to parse technical requirements, saving `JobRequirement` rows.
2. **Skill Gap Analysis:**
   - Client requests `POST /skill-gap/analyze/{job_id}` (`backend/app/api/routes/skill_gap.py`).
   - `skill_gap_engine.analyze_skill_gap` fetches user skills (`UserSkill`) and job requirements.
   - For each requirement, `skill_matching_service.py` executes exact matching, followed by semantic vector cosine comparison via `EmbeddingService.cosine_similarity` (`backend/app/services/embedding_service.py`).
   - Each requirement is classified into `MatchClassification` (`strong`, `partial`, `transferable`, `gap`) with a assigned `PriorityLevel`.
   - Explanations are attached and results saved to `skill_gap_analyses` and `skill_gap_results`.
3. **Roadmap Generation:**
   - Client requests `POST /roadmaps` (`backend/app/api/routes/roadmaps.py`) with weekly hours and duration constraints.
   - `roadmap_service.generate_and_store` reads verified gaps from the analysis.
   - `planner.plan_roadmap` evaluates prerequisites via `DEPENDENCIES` graph (`backend/app/core/roadmap_config.py`), assigns hours, fits items within capacity, and marks deferred items.
   - `roadmap_llm.generate_roadmap_content` requests learning topics and practical exercises from Gemini; if invalid or timed out, repairs items using deterministic templates.
   - Persists `Roadmap` and ordered `RoadmapItem` rows.
4. **Career Readiness Tracking:**
   - When users mark progress or link GitHub evidence (`POST /evidence`), `readiness_engine.compute_readiness` evaluates the 5 weighted components (`alignment`, `required_coverage`, `evidence`, `gap_health`, `roadmap`), updating `readiness_snapshots`.

**State Management:**
- Backend: Stateless HTTP API with JWT tokens passed per request; state persisted in PostgreSQL.
- Frontend: `AuthContext` (`frontend/src/context/AuthContext.jsx`) stores current user and tokens in React state and `localStorage`.

## Key Abstractions

**MatchClassification:**
- Purpose: Standard taxonomy of how well a user's skill matches a job requirement.
- Values: `strong` (direct proficiency), `partial` (intermediate or related), `transferable` (adjacent foundation), `gap` (missing).
- Defined in: `backend/app/models/skill_gap.py`

**Roadmap Planner DAG:**
- Purpose: Models prerequisite relationships between technical skills (e.g. Python -> FastAPI -> REST API).
- Implementation: Directed graph cycle check, topological ordering, and capacity-constrained bin-packing in `backend/app/services/roadmap/planner.py`.

**Career Readiness Formula:**
- Purpose: Transparent single composite readiness metric (0-100) combining alignment score, coverage of required skills, validated code evidence, remaining gap health, and roadmap progress.
- Defined in: `backend/app/core/readiness_config.py`, executed in `backend/app/services/readiness_engine.py`.

## Entry Points

**Backend Application:**
- Location: `backend/app/main.py`
- Invocation: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Triggers: HTTP requests dispatched to FastAPI routers.

**Frontend Application:**
- Location: `frontend/src/main.jsx` -> `frontend/src/App.jsx`
- Invocation: `npm run dev` (Vite dev server on `http://localhost:5173`)
- Triggers: Browser document load.

## Architectural Constraints

- **Execution Model:** Synchronous endpoints (`def`) inside FastAPI to avoid blocking event loops during CPU-bound embedding vector generation or synchronous SQLAlchemy DB sessions.
- **Global State & Singletons:**
  - `_client = genai.Client(...)` module-level client in `backend/app/services/gemini_service.py`.
  - `EmbeddingService` single instance in `backend/app/services/embedding_service.py` caching loaded PyTorch models.
- **Environment Dependency:** `backend/app/core/config.py` directly executes `Settings()` at import time, requiring `.env` or system environment variables to be populated immediately upon module import.

## Anti-Patterns

### Import-Time Configuration Execution
**What happens:** `settings = Settings()` is invoked globally in `backend/app/core/config.py` during module evaluation.
**Why it's wrong:** Any test or script importing `app.*` from a directory other than `backend/` fails immediately if environment variables are not globally exported.
**Do this instead:** Use lazy settings instantiation or fallback defaults for non-sensitive testing configurations.

### Synchronous Network Calls Inside Route Handlers
**What happens:** Direct synchronous HTTP requests to GitHub API or Gemini API occur within request execution.
**Why it's wrong:** External API latencies or outages directly inflate client response time.
**Do this instead:** Keep robust timeouts (as currently present in `roadmap_llm.py`) and fallback gracefully to deterministic outputs.

## Error Handling

**Strategy:** Fail gracefully with informative HTTP status codes; use typed domain exceptions for recoverable subsystem failures.

**Patterns:**
- `EmbeddingServiceUnavailable` caught in `skill_matching_service.py` to fall back to exact matching.
- `GitHubUnavailable` caught in `evidence_service.py` marking verification status as `unavailable` without crashing.
- `HTTPException` raised at route boundaries for client errors (400, 401, 404, 502).

## Cross-Cutting Concerns

**Logging:** Standard library `logging.getLogger(__name__)` used across services.
**Validation:** Pydantic models in `backend/app/schemas/` validate request payload shapes, string lengths, and numeric ranges.
**Authentication:** Fast-failing JWT validation via `app.dependencies.auth.get_current_user` injected as a dependency across all protected endpoints.

---

*Architecture analysis: 2026-11-01*

