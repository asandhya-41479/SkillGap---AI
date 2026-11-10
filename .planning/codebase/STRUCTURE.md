# Codebase Structure

**Analysis Date:** 2026-11-01

## Directory Layout

```text
skillgap-ai/
├── .agent/                    # GSD workflows, agent prompts, and custom skills
├── .planning/                 # Project memory, codebase maps, roadmaps, and execution tracking
│   └── codebase/              # Structured codebase reference documentation
├── backend/                   # FastAPI backend server application
│   ├── app/                   # Core application package
│   │   ├── api/               # API routes and presentation endpoints
│   │   │   └── routes/        # Modular API route controllers
│   │   ├── core/              # Global configuration, security helpers, rule constants
│   │   ├── db/                # SQLAlchemy database connection and declarative base
│   │   ├── dependencies/      # FastAPI dependency providers (e.g. auth guard)
│   │   ├── models/            # SQLAlchemy 2.0 ORM database entity definitions
│   │   ├── schemas/           # Pydantic validation request and response models
│   │   ├── services/          # Business logic, ML models, analysis engines
│   │   │   └── roadmap/       # Roadmap deterministic planner and LLM integration
│   │   ├── utils/             # Helper utilities
│   │   └── main.py            # FastAPI application factory and entry point
│   ├── migrations/            # SQL migration scripts for schema updates
│   ├── tests/                 # Backend automated test suite (pytest)
│   ├── .env.example           # Example environment variable template
│   └── requirements.txt       # Python package dependencies
├── frontend/                  # React 19 Single Page Application (SPA)
│   ├── public/                # Static assets served without bundling
│   ├── src/                   # React source code
│   │   ├── api/               # Axios API client modules per resource
│   │   ├── assets/            # Component graphics, logos, and SVGs
│   │   ├── components/        # Reusable UI component modules
│   │   │   ├── jobs/          # Job intake and requirements components
│   │   │   ├── roadmap/       # Roadmap cards and timeline controls
│   │   │   ├── skillgap/      # Skill match rows and gap visualization
│   │   │   └── skills/        # Skill forms, tables, and GitHub connect cards
│   │   ├── context/           # React context providers (AuthContext)
│   │   ├── pages/             # Route-level page components
│   │   ├── App.css            # Global CSS overrides
│   │   ├── App.jsx            # Top-level route switch and route guards
│   │   ├── index.css          # Tailwind CSS root directives
│   │   └── main.jsx           # React DOM client entry mount
│   ├── package.json           # Frontend dependency declarations and scripts
│   └── vite.config.js         # Vite bundler configuration
├── docs/                      # General project documentation
└── .gitignore                 # Root git ignore specification
```

## Directory Purposes

**`backend/app/api/routes/`:**
- Purpose: HTTP endpoint definitions grouped by resource.
- Contains: `auth.py`, `users.py`, `skills.py`, `github.py`, `jobs.py`, `skill_gap.py`, `roadmaps.py`, `evidence.py`, `readiness.py`, `profile.py`.
- Key files: `roadmaps.py`, `skill_gap.py`, `auth.py`.

**`backend/app/core/`:**
- Purpose: Global configuration and deterministic domain rule definitions.
- Contains: Environment settings (`config.py`), auth/jwt utilities (`security.py`), roadmap effort/prerequisite configs (`roadmap_config.py`), readiness weights and formula settings (`readiness_config.py`).

**`backend/app/models/`:**
- Purpose: Relational database table declarations using SQLAlchemy 2.0.
- Key files: `user.py`, `skill.py`, `job.py`, `skill_gap.py`, `roadmap.py`, `readiness.py`, `github_connection.py`.

**`backend/app/schemas/`:**
- Purpose: Data validation, deserialization, and serialization contracts.
- Key files: `roadmap.py`, `readiness.py`, `job.py`, `skill_gap.py`, `user.py`.

**`backend/app/services/`:**
- Purpose: Domain business logic decoupled from HTTP transport.
- Key files: `skill_gap_engine.py`, `skill_matching_service.py`, `embedding_service.py`, `gemini_service.py`, `job_service.py`, `readiness_engine.py`, `evidence_service.py`.

**`backend/app/services/roadmap/`:**
- Purpose: Isolated subsystem for generating, sizing, scheduling, and LLM-enriching learning roadmaps.
- Key files: `planner.py` (DAG dependency engine), `dependency_graph.py`, `effort.py`, `roadmap_llm.py` (Gemini integration), `roadmap_service.py` (CRUD & lifecycle).

**`frontend/src/pages/`:**
- Purpose: Top-level views mounted by React Router.
- Key files: `Dashboard.jsx`, `JobIntelligence.jsx`, `SkillGapAnalysis.jsx`, `Roadmap.jsx`, `SkillProfile.jsx`, `Login.jsx`, `Register.jsx`.

**`frontend/src/components/`:**
- Purpose: Modular presentational and container components grouped by feature area.
- Contains: `jobs/`, `roadmap/`, `skillgap/`, `skills/`, `ProtectedRoute.jsx`.

**`frontend/src/api/`:**
- Purpose: HTTP communication layer using Axios with automatic auth token header injection.
- Key files: `axios.js`, `jobs.js`, `roadmaps.js`, `skillGap.js`, `skills.js`, `github.js`.

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: ASGI FastAPI entry point and router aggregator
- `frontend/src/main.jsx`: Browser DOM mount point
- `frontend/src/App.jsx`: SPA Router root declaration

**Configuration:**
- `backend/app/core/config.py`: Backend environment settings
- `backend/app/core/roadmap_config.py`: Roadmap rule engine rules, hours, prerequisites
- `backend/app/core/readiness_config.py`: Career readiness formula parameters
- `frontend/vite.config.js`: Vite build configuration

**Core Domain Logic:**
- `backend/app/services/skill_gap_engine.py`: Skill gap classification engine
- `backend/app/services/roadmap/planner.py`: Prerequisite topological sorter and scheduler
- `backend/app/services/readiness_engine.py`: Career readiness computation engine
- `backend/app/services/embedding_service.py`: Local vector embedding provider

**Testing:**
- `backend/tests/`: All backend pytest test files (`test_roadmap_rule_engine.py`, `test_readiness_engine.py`, etc.)

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` (e.g. `roadmap_service.py`, `skill_gap.py`)
- Frontend Components: `PascalCase.jsx` (e.g. `RoadmapItemCard.jsx`, `SkillForm.jsx`)
- Frontend Utilities/APIs: `camelCase.js` (e.g. `skillGap.js`, `axios.js`)
- Test Files: `test_<module>.py` in `backend/tests/`

**Code Symbols:**
- Python Classes: `PascalCase` (e.g. `RoadmapItem`, `SkillGapResult`)
- Python Functions/Methods: `snake_case()` (e.g. `analyze_skill_gap`, `create_access_token`)
- Python Enums: `PascalCase` class, `snake_case` or lowercase string members (`MatchClassification.gap`)
- React Components: `PascalCase` (e.g. `JobIntelligence`, `Roadmap`)
- React Hooks/Functions: `camelCase` (e.g. `useAuth`, `handleLogout`)

## Where to Add New Code

**New API Endpoint:**
- Router: Add route handler in `backend/app/api/routes/<feature>.py` (or create a new route module and include in `backend/app/main.py`)
- Schema: Define request/response Pydantic models in `backend/app/schemas/<feature>.py`
- Logic: Implement business rules in `backend/app/services/<feature>_service.py`
- Test: Add test cases to `backend/tests/test_<feature>_api.py`

**New Database Entity / Migration:**
- Model: Define SQLAlchemy model in `backend/app/models/<entity>.py` and re-export in `backend/app/models/__init__.py`
- Schema Change: Add DDL to `backend/migrations/` if modifying existing tables (since `Base.metadata.create_all` does not alter existing columns)

**New Frontend View / Feature:**
- Page: Create component in `frontend/src/pages/<PageName>.jsx`
- Route: Register route and protection wrapper in `frontend/src/App.jsx`
- API Client: Add endpoint call to `frontend/src/api/<resource>.js`
- Sub-components: Place modular UI pieces in `frontend/src/components/<feature>/`

**Utilities / Shared Helpers:**
- Backend: Shared logic in `backend/app/utils/`
- Frontend: Shared components in `frontend/src/components/`, API client config in `frontend/src/api/`

## Special Directories

**`.planning/`:**
- Purpose: Contains GSD project specifications, phase plans, requirements, and codebase intelligence
- Generated: Semi-automated by GSD workflows
- Committed: Yes

**`backend/migrations/`:**
- Purpose: Contains manual and historical SQL migration files (e.g. `module6.sql`)
- Generated: No (manually authored)
- Committed: Yes

**`backend/app/api/routes/__pycache__/`:**
- Purpose: Python bytecode cache
- Note: A rogue source file `roadmaps.py` was detected inside this directory and should be cleaned up.

---

*Structure analysis: 2026-11-01*

