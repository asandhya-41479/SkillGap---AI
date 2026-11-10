# Coding Conventions

**Analysis Date:** 2026-11-01

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` (`roadmap_service.py`, `skill_gap_engine.py`, `evidence.py`)
- Frontend Components: `PascalCase.jsx` (`RoadmapItemCard.jsx`, `JobIntelligence.jsx`, `SkillForm.jsx`)
- Frontend API/Services: `camelCase.js` (`jobs.js`, `skillGap.js`, `axios.js`)
- Unit & API Tests: `test_<feature>.py` (`test_evidence.py`, `test_roadmap_rule_engine.py`)

**Classes & Types:**
- Python Classes: `PascalCase` (`User`, `RoadmapItem`, `SkillGapAnalysis`, `EmbeddingService`)
- Python Enums: `PascalCase` subclassing `(str, enum.Enum)` with lowercase or `snake_case` string values:
  ```python
  class MatchClassification(str, enum.Enum):
      strong = "strong"
      partial = "partial"
      transferable = "transferable"
      gap = "gap"
  ```
- Pydantic Schemas: `PascalCase` with descriptive suffixes (`RoadmapCreate`, `RoadmapDetailResponse`, `UserLogin`)

**Functions & Methods:**
- Python: `snake_case` with descriptive verbs (`create_user`, `analyze_skill_gap`, `generate_and_store`, `to_detail`)
- React Component Functions: `PascalCase` (`function Dashboard()`, `const ResultRow = (...) =>`)
- React Handlers & Hooks: `camelCase` with standard prefixes (`handleLogout`, `handleSubmit`, `useAuth`)

**Variables & Constants:**
- Global Constants & Configuration: `UPPER_SNAKE_CASE` (`HOURS_BY_SIZE`, `DEPENDENCIES`, `COMPONENT_WEIGHTS`, `FORMULA_VERSION`)
- Local Variables: `snake_case` in Python (`user_id`, `analysis_id`, `scheduled_items`); `camelCase` in JavaScript (`jobId`, `accessToken`, `targetRole`)

## Code Style

**Formatting & Linting:**
- Python: PEP 8 standard formatting with explicit type hints (`Mapped[int]`, `list[dict]`, `Optional[str]`).
- JavaScript/React: Linted via `oxlint` (`frontend/package.json`). Clean functional components utilizing React hooks.

**Type Annotations (Python):**
- Modern Python 3.10+ union and collection syntax preferred (`str | None`, `list[str]`, `dict[str, float]`).
- Explicit SQLAlchemy 2.0 ORM column mapping annotations:
  ```python
  id: Mapped[int] = mapped_column(primary_key=True, index=True)
  name: Mapped[str] = mapped_column(String(100), nullable=False)
  ```

## Import Organization

**Python Module Import Order:**
1. Standard library modules:
   ```python
   import enum
   from datetime import datetime, timezone
   from typing import Optional
   ```
2. Third-party dependencies:
   ```python
   from fastapi import APIRouter, Depends, HTTPException, status
   from sqlalchemy.orm import Session
   from google import genai
   ```
3. First-party internal packages:
   ```python
   from app.core.config import settings
   from app.db.database import get_db
   from app.models.user import User
   from app.services.roadmap import roadmap_service as svc
   ```

**Frontend React Import Order:**
1. React and third-party libraries (`react`, `react-router-dom`, `axios`)
2. Context and global state (`../context/AuthContext`)
3. API client modules (`../api/jobs`, `../api/roadmaps`)
4. Child components and assets (`../components/jobs/JobForm`)

**Path Aliases:**
- Backend relies on absolute package root imports (`from app.core.config import settings` where `backend/` is on `sys.path`).
- Frontend uses standard relative directory paths (`../components/`, `./pages/`).

## Error Handling

**FastAPI Route Boundary:**
- Raise explicit `HTTPException` with semantic HTTP status codes:
  ```python
  if user is None:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid email or password",
      )
  ```

**Domain Exception Hierarchy:**
- Service layers define custom typed exceptions for recoverable or expected external failures:
  ```python
  class EmbeddingServiceUnavailable(Exception):
      """Raised when the embedding model failed to load or encode."""

  class GitHubUnavailable(Exception):
      """Raised when GitHub REST API fails or is unreachable."""
  ```

**External LLM & JSON Safeguards:**
- Always strip markdown fences (` ```json `) and validate raw string responses before decoding:
  ```python
  if raw_text.startswith("```"):
      raw_text = raw_text.strip("`")
      if raw_text.startswith("json"):
          raw_text = raw_text[4:]
      raw_text = raw_text.strip()
  ```
- Catch `json.JSONDecodeError` and fall back to deterministic rule templates rather than crashing the pipeline.

## Logging

**Framework:** Standard library `logging.getLogger(__name__)`.

**Patterns:**
- Log exceptions before raising typed domain errors:
  ```python
  logger.exception("Failed to load embedding model")
  raise EmbeddingServiceUnavailable(str(exc)) from exc
  ```
- Log external service lifecycle events at `INFO` level.
- Avoid logging sensitive credentials, JWT secrets, or raw passwords.

## Comments & Documentation

**Module Docstrings:**
- Prominently placed at the top of domain engines explaining design boundaries and step affiliations:
  ```python
  """Static rules for the Module 5 roadmap rule engine.
  Everything here is deterministic and reviewable.
  """
  ```

**Inline Notes:**
- Used to document regulatory or business rules (e.g. `# Module 6: True when gap was raised to partial due to evidence`).

## Function Design

**Determinism First:**
- Separate computation engines (pure input-output functions like `plan_roadmap`, `compute_readiness`) from database persistence functions (`generate_and_store`, `save_evidence`).

**Parameter Typing:**
- Pass typed schemas or models rather than arbitrary kwargs.
- DB sessions injected as the last parameter in service calls: `def generate_and_store(db: Session, user_id: int, data: RoadmapCreate)`.

---

*Convention analysis: 2026-11-01*

