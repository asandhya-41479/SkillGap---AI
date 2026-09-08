from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db.base import Base


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    github_username = Column(String(100), nullable=False)
    github_user_id = Column(Integer, nullable=False)
    access_token = Column(String(500), nullable=False)

    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_synced_at = Column(DateTime, nullable=True)