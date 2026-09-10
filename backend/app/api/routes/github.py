from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.github import GitHubConnectionStatus
from app.services import github_service

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/connect")
def connect_github(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    authorize_url = github_service.create_authorize_url(db, current_user.id)
    return {"authorize_url": authorize_url}


@router.get("/callback")
async def github_callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    user_id = github_service.validate_and_consume_state(db, state)
    access_token = await github_service.exchange_code_for_token(code)
    profile = await github_service.fetch_github_profile(access_token)

    github_service.upsert_github_connection(
        db,
        user_id=user_id,

        github_username=profile["login"],
        github_user_id=profile["id"],
        access_token=access_token,
    )

    return RedirectResponse(url=settings.github_frontend_redirect)


@router.get("/status", response_model=GitHubConnectionStatus)
def github_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connection = github_service.get_connection_status(db, current_user.id)
    if connection is None:
        return GitHubConnectionStatus(connected=False)
    return GitHubConnectionStatus(
        connected=True,
        github_username=connection.github_username,
        last_synced_at=connection.last_synced_at,
    )