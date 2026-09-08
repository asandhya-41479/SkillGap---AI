from datetime import datetime

from pydantic import BaseModel


class GitHubConnectionStatus(BaseModel):
    connected: bool
    github_username: str | None = None
    last_synced_at: datetime | None = None