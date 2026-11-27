from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.core.time import utcnow
from app.db.base import Base


class PasswordResetToken(Base):
    """One "forgot password" link. Only a SHA-256 hash of the token is stored, never the token itself,
    so a database leak cannot be used to reset anyone's password. Single use, short expiry."""

    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
