import logging

from fastapi import HTTPException
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.github import GitHubConnectionStatus
from app.services import github_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/connect")
def connect_github(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    authorize_url = github_service.create_authorize_url(db, current_user.id)
    return {"authorize_url": authorize_url}


def _back_to_app(result: str) -> RedirectResponse:
    """Always return the user to the website, with ?github=connected or ?github=error.

    Before this, a failed callback showed a raw JSON error on the backend's address and the
    user lost the app. The reason is logged on the server, never put in the URL.
    """
    base = settings.github_frontend_redirect
    sep = "&" if "?" in base else "?"
    return RedirectResponse(url=f"{base}{sep}github={result}")


@router.get("/callback")
async def github_callback(
    code: str | None = Query(None), state: str | None = Query(None), db: Session = Depends(get_db),
):
    # GitHub sends no code when the user clicks "Cancel" (it sends ?error=access_denied instead).
    if not code or not state:
        return _back_to_app("error")
    try:
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
    except Exception:
        logger.warning("GitHub OAuth callback failed", exc_info=True)
        return _back_to_app("error")

    return _back_to_app("connected")


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

@router.get("/repositories")
async def list_repositories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connection = github_service.get_connection_status(db, current_user.id)
    if connection is None:
        raise HTTPException(status_code=400, detail="GitHub account not connected.")
    repos = await github_service.fetch_user_repos(connection.access_token)
    return [{"name": r["name"], "url": r["html_url"], "language": r["language"], "topics": r.get("topics", [])} for r in repos]


@router.post("/analyze")
async def analyze(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return await github_service.analyze_repositories(db, current_user.id)