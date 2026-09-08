from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine
from app.db.base import Base
from app.models import user  # noqa: F401
from app.models import skill  # noqa: F401  (registers UserSkill, SkillEvidence)
from app.models import github_connection  # noqa: F401  (registers GitHubConnection)
from app.api.routes import auth, users

app = FastAPI(title="SkillGap AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():

    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "SkillGap AI Backend is running"}