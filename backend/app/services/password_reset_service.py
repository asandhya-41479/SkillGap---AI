"""Forgot password: create a single-use reset link, email it, and set the new password.

Security rules:
- The answer to "forgot password" is always the same, so it never reveals whether an email is registered.
- The token is 32 random bytes (secrets.token_urlsafe); only its SHA-256 hash is stored.
- A link expires after PASSWORD_RESET_MINUTES (default 30) and works once. Asking again cancels older links.
- At most MAX_REQUESTS reset emails per address per hour (in memory, like the login limit).
- A successful reset also clears the login rate limit for that email.
"""
import hashlib
import html
import logging
import secrets
import threading
import time
from collections import deque
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.login_limiter import login_limiter
from app.core.security import hash_password
from app.core.time import utcnow
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

MAX_REQUESTS = 3
WINDOW_SECONDS = 60 * 60
INVALID_LINK = "This reset link is invalid or has expired. Please request a new one."


class ResetRequestLimiter:
    """At most `max_requests` reset emails per email address within `window` seconds."""

    def __init__(self, max_requests: int = MAX_REQUESTS, window: int = WINDOW_SECONDS, clock=time.monotonic):
        self.max, self.window, self.clock = max_requests, window, clock
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, email: str) -> bool:
        key, now = email.strip().lower(), self.clock()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= self.max:
                return False
            q.append(now)
            return True


reset_request_limiter = ResetRequestLimiter()


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def reset_link(token: str) -> str:
    return f"{settings.frontend_origin.rstrip('/')}/reset-password?token={token}"


def create_reset_token(db: Session, user: User) -> str:
    """Cancels this user's unused links, stores a new hashed token and returns the plain token."""
    now = utcnow()
    for old in db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
    ):
        old.used_at = now
    token = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=_hash(token),
        expires_at=now + timedelta(minutes=settings.password_reset_minutes),
    ))
    db.commit()
    return token


def build_email(name: str, link: str) -> tuple[str, str, str]:
    minutes = settings.password_reset_minutes
    subject = "Reset your SkillGap AI password"
    text = (
        f"Hi {name},\n\nWe received a request to reset your SkillGap AI password.\n"
        f"Open this link to choose a new password (valid for {minutes} minutes, works once):\n\n{link}\n\n"
        "If you did not ask for this, you can ignore this email; your password stays the same.\n"
    )
    safe_name, safe_link = html.escape(name), html.escape(link, quote=True)
    body = (
        f'<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#0F172A">'
        f'<h2 style="color:#0A2540">Reset your password</h2>'
        f"<p>Hi {safe_name},</p><p>We received a request to reset your SkillGap AI password.</p>"
        f'<p><a href="{safe_link}" style="display:inline-block;background:#2563EB;color:#fff;padding:12px 22px;'
        f'border-radius:10px;text-decoration:none;font-weight:bold">Choose a new password</a></p>'
        f"<p style=\"color:#475569;font-size:14px\">The link is valid for {minutes} minutes and works once. "
        "If you did not ask for this, ignore this email; your password stays the same.</p></div>"
    )
    return subject, body, text


def request_reset(db: Session, email: str) -> None:
    """Sends a reset email when the account exists and the limit allows. Returns nothing either way."""
    if not reset_request_limiter.allow(email):
        logger.info("Password reset request limited.")
        return
    user = db.query(User).filter(User.email == email.strip()).first()
    if user is None:
        return
    token = create_reset_token(db, user)
    subject, body, text = build_email(user.name, reset_link(token))
    if not send_email(user.email, subject, body, text):
        logger.warning("Password reset email for user id %s was not sent.", user.id)


def reset_password(db: Session, token: str, new_password: str) -> User:
    """Sets the new password if the token is valid. Raises ValueError(INVALID_LINK) otherwise."""
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == _hash(token)).first()
    now = utcnow()
    if row is None or row.used_at is not None or row.expires_at < now:
        raise ValueError(INVALID_LINK)
    user = db.get(User, row.user_id)
    if user is None:
        raise ValueError(INVALID_LINK)
    user.password_hash = hash_password(new_password)
    row.used_at = now
    db.commit()
    login_limiter.reset(user.email)
    return user
