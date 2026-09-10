import secrets
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.github_connection import GitHubConnection
from app.models.oauth_state import OAuthState

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

STATE_EXPIRY_MINUTES = 10


def create_authorize_url(db: Session, user_id: int) -> str:
    db.query(OAuthState).filter(OAuthState.user_id == user_id).delete()

    state = secrets.token_urlsafe(32)
    db.add(OAuthState(state=state, user_id=user_id))
    db.commit()

    params = (
        f"client_id={settings.github_client_id}"
        f"&redirect_uri={settings.github_redirect_uri}"
        f"&scope=read:user"
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
    async with httpx.AsyncClient() as client:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to obtain GitHub access token.",
        )
    return access_token


async def fetch_github_profile(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fetch GitHub profile.",
        )
    return response.json()


def upsert_github_connection(
    db: Session, user_id: int, github_username: str, github_user_id: int, access_token: str
) -> GitHubConnection:
    connection = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()

    if connection is None:
        connection = GitHubConnection(
            user_id=user_id,
            github_username=github_username,
            github_user_id=github_user_id,
            access_token=access_token,
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