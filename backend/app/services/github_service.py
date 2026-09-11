import secrets
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.github_connection import GitHubConnection
from app.models.oauth_state import OAuthState
from app.models.skill import DetectedVia, EvidenceSource, SkillCategory, SkillEvidence, UserSkill
from app.services.skill_normalization import normalize_skill_name

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_TIMEOUT = httpx.Timeout(15.0)

STATE_EXPIRY_MINUTES = 10


def create_authorize_url(db: Session, user_id: int) -> str:
    db.query(OAuthState).filter(OAuthState.user_id == user_id).delete()

    state = secrets.token_urlsafe(32)
    db.add(OAuthState(state=state, user_id=user_id))
    db.commit()

    params = (
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
                f"&scope=read:user public_repo"

        f"&state={state}"
    )
    return f"{GITHUB_AUTHORIZE_URL}?{params}"


def validate_and_consume_state(db: Session, state: str) -> int:
    state_row = db.query(OAuthState).filter(OAuthState.state == state).first()

    if state_row is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state.")

    if datetime.utcnow() - state_row.created_at > timedelta(minutes=STATE_EXPIRY_MINUTES):
        db.delete(state_row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state expired.")

    user_id = state_row.user_id
    db.delete(state_row)
    db.commit()
    return user_id


async def exchange_code_for_token(code: str) -> str:
    async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT) as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,

            },
        )
    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain GitHub access token.")
    return access_token


async def fetch_github_profile(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT) as client:
        response = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch GitHub profile.")
    return response.json()


def upsert_github_connection(
    db: Session, user_id: int, github_username: str, github_user_id: int, access_token: str
) -> GitHubConnection:
    connection = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()

    if connection is None:
        connection = GitHubConnection(
            user_id=user_id, github_username=github_username,
            github_user_id=github_user_id, access_token=access_token,
        )
        db.add(connection)
    else:

        connection.github_username = github_username
        connection.github_user_id = github_user_id
        connection.access_token = access_token
        connection.connected_at = datetime.utcnow()

    db.commit()
    db.refresh(connection)
    return connection


def get_connection_status(db: Session, user_id: int) -> GitHubConnection | None:
    return db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()


async def fetch_user_repos(access_token: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT) as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
            params={"per_page": 50, "sort": "pushed"},
        )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch GitHub repositories.")
    return response.json()


def _record_evidence(db: Session, user_id: int, raw_name: str, category: SkillCategory, repo: dict, via: DetectedVia):
    name = normalize_skill_name(raw_name)
    skill = db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_name == name).first()
    if skill is None:
        skill = UserSkill(user_id=user_id, skill_name=name, category=category, is_manual=False)
        db.add(skill)

        db.flush()  # get skill.id without a full commit yet
    db.add(SkillEvidence(
        user_skill_id=skill.id, source=EvidenceSource.github,
        repo_name=repo["name"], repo_url=repo["html_url"], detected_via=via,
    ))


async def analyze_repositories(db: Session, user_id: int) -> dict:
    connection = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()
    if connection is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub account not connected.")

    headers = {"Authorization": f"Bearer {connection.access_token}", "Accept": "application/vnd.github+json"}

    async with httpx.AsyncClient(timeout=GITHUB_TIMEOUT, headers=headers) as client:
        resp = await client.get("https://api.github.com/user/repos", params={"per_page": 50, "sort": "pushed"})
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub repositories.")
        repos = resp.json()

        db.query(SkillEvidence).filter(
            SkillEvidence.source == EvidenceSource.github,
            SkillEvidence.user_skill_id.in_(db.query(UserSkill.id).filter(UserSkill.user_id == user_id)),
        ).delete(synchronize_session=False)

        for repo in repos:
            lang_resp = await client.get(repo["languages_url"])
            languages = lang_resp.json() if lang_resp.status_code == 200 else {}
            for lang in languages:
                _record_evidence(db, user_id, lang, SkillCategory.programming_language, repo, DetectedVia.language)
            for topic in repo.get("topics", []):
                _record_evidence(db, user_id, topic, SkillCategory.tool, repo, DetectedVia.topic)


    connection.last_synced_at = datetime.utcnow()
    db.commit()
    return {"repositories_analyzed": len(repos)}
