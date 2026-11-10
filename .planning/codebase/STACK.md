# Technology Stack

**Analysis Date:** 2026-11-01

## Languages

**Primary:**
- Python 3.13.15 - Backend API, business logic, ML/NLP services, data models, rule engines in `backend/app/`
- JavaScript (ES Modules, React 19 JSX) - Frontend SPA UI components, pages, state context, and API clients in `frontend/src/`

**Secondary:**
- SQL (PostgreSQL dialect) - Database migrations and schema definitions in `backend/migrations/` and SQLAlchemy models
- HTML5 / CSS3 - Tailwind CSS v4 styling in `frontend/src/App.css`, `frontend/src/index.css`

## Runtime

**Environment:**
- Python 3.13.15 running in virtualenv `backend/.venv`
- Node.js v24.19.0 (with browser ES2022+ targeting)

**Package Manager:**
- Python: `pip` (backend dependencies managed in `backend/requirements.txt`)
  - Lockfile: missing (direct `requirements.txt` pinning)
- JavaScript: `npm` 11.17.0
  - Lockfile: present (`frontend/package-lock.json`)

## Frameworks

**Core:**
- FastAPI 0.141.1 (`backend/app/main.py`) - REST API server, routing, dependency injection, OpenAPI documentation
- Starlette 1.6.0 - Underlying ASGI toolkit for FastAPI
- Pydantic 2.13.4 & `pydantic-settings` 2.15.0 - Request/response schemas, validation, environment configuration
- React 19.2.8 (`frontend/src/main.jsx`) - Frontend component rendering and reactive state
- React Router DOM 7.18.2 (`frontend/src/App.jsx`) - Client-side SPA routing and navigation guards

**Testing:**
- pytest (version in `backend/.venv`) - Backend unit and API testing (`backend/tests/`)
- Frontend testing: none configured (no Vitest or Jest installed)

**Build/Dev:**
- Vite 8.2.0 (`frontend/vite.config.js`) - Frontend module bundler and local development server
- Tailwind CSS 4.3.3 (`@tailwindcss/vite` 4.3.3) - Utility-first styling engine
- Oxlint 1.75.0 (`frontend/package.json`) - High-performance JavaScript linter
- Uvicorn 0.52.2 - ASGI web server for FastAPI

## Key Dependencies

**Critical:**
- `SQLAlchemy` 2.0.52 (`backend/app/db/base.py`, `backend/app/db/database.py`) - SQL toolkit and Object Relational Mapper for PostgreSQL / SQLite
- `psycopg2-binary` 2.9.12 - PostgreSQL database adapter
- `google-genai` 2.18.0 & `google-ai-generativelanguage` 0.6.15 (`backend/app/services/gemini_service.py`, `backend/app/services/roadmap/roadmap_llm.py`) - Official Google GenAI SDK for Gemini 3.6 Flash / 2.5 models
- `sentence-transformers` 6.1.0 & `torch` 2.14.0 (`backend/app/services/embedding_service.py`) - Local sentence embedding generation (`all-MiniLM-L6-v2`) for semantic skill gap calculation (Note: installed in `.venv` but omitted from `requirements.txt`)
- `PyMuPDF` (fitz) 1.28.2 & `python-docx` 1.2.0 - Resume document text extraction and parsing
- `passlib` 1.7.4 (bcrypt 4.0.1) & `python-jose` 3.5.0 / `PyJWT` 2.13.0 (`backend/app/core/security.py`) - Cryptographic password hashing and JWT token issuance / verification
- `axios` 1.19.0 (`frontend/src/api/axios.js`) - Promise-based HTTP client with request authorization interceptors

**Infrastructure & Utilities:**
- `supabase` 2.31.0 (`postgrest`, `realtime`, `storage3`, `supabase-auth`) - Supabase client libraries
- `httpx` 0.28.1 & `aiohttp` 3.14.3 - Asynchronous HTTP clients for external GitHub / third-party API communication
- `numpy` 2.5.2 - Vector mathematics and cosine similarity in embedding services

## Configuration

**Environment:**
- Backend: `backend/app/core/config.py` defines `Settings(BaseSettings)` which reads from `backend/.env`.
  - Required environment variables: `DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_ORIGIN`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`, `GITHUB_FRONTEND_REDIRECT`, `GEMINI_API_KEY`.
  - `.env` file present in `backend/` (uncommitted); reference template in `backend/.env.example`.
- Frontend: Vite environment variables accessed via `import.meta.env` (e.g. `VITE_API_URL` configured in `frontend/src/api/axios.js`).

**Build:**
- Frontend: `frontend/vite.config.js` sets up React and Tailwind plugins
- Backend: Standard Python module layout; migrations located in `backend/migrations/`

## Platform Requirements

**Development:**
- Windows / Linux / macOS with Python 3.13+ and Node.js 20+
- Active PostgreSQL database (or Supabase instance) accessible via `DATABASE_URL`
- GitHub OAuth App registered for OAuth authentication flows
- Google Gemini API key

**Production:**
- Backend: Containerized ASGI deployment (Docker / Cloud Run / VPS) running Uvicorn behind reverse proxy
- Frontend: Static asset hosting (Vercel, Netlify, Cloudflare Pages, S3/CloudFront) with `VITE_API_URL` pointing to backend

---

*Stack analysis: 2026-11-01*

