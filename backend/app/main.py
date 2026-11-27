from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.openapi import API_DESCRIPTION, TAGS, apply_documentation
from app.db.base import Base
from app.db.database import engine

# Importing every model module registers its tables on Base.metadata before create_all().
from app.models import (  # noqa: F401
    career,            # Module 7: plans, actions, interview prep, opportunity matches
    github_connection,
    job,
    password_reset,    # forgot-password links (hashed, single use)
    readiness,         # Module 6: evidence, readiness snapshots
    roadmap,           # Module 5: roadmaps and items
    skill,
    skill_gap,         # Module 4: analyses and results
    user,
)
from app.api.routes import (
    auth,
    career as career_routes,
    evidence,
    github,
    jobs,
    profile,
    readiness as readiness_routes,
    roadmaps,
    skill_gap as skill_gap_routes,
    skills,
    users,
)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Creates missing tables on startup. It never alters existing tables: new columns get a
    # one-off script in backend/scripts/ (see add_requirement_alternatives.py).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SkillGap AI API",
    version="1.0.0",
    description=API_DESCRIPTION,
    openapi_tags=TAGS,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

_ROUTERS = [m.router for m in (auth, users, skills, profile, github, jobs, skill_gap_routes, roadmaps,
                                evidence, readiness_routes, career_routes)]
apply_documentation(*_ROUTERS)          # before include_router (see apply_documentation)
for router in _ROUTERS:
    app.include_router(router)


@app.get("/health", tags=["SYSTEM"], summary="Health check")
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "SkillGap AI Backend is running"}
