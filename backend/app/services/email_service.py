"""Sends transactional email through Brevo's HTTPS API.

Why HTTPS and not SMTP: Render's free plan blocks outbound SMTP ports (25, 465, 587), so Gmail SMTP
would work locally but fail in production. Brevo's REST API uses port 443, which is allowed.

If BREVO_API_KEY or EMAIL_FROM is not set, nothing is sent and the function returns False.
"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def email_configured() -> bool:
    return bool(settings.brevo_api_key.strip() and settings.email_from.strip())


def send_email(to_email: str, subject: str, html: str, text: str) -> bool:
    """Returns True when Brevo accepted the message. Never raises: email problems are logged, because
    the caller (forgot password) must give the same answer whether or not an email went out."""
    if not email_configured():
        logger.warning("Email not sent: BREVO_API_KEY / EMAIL_FROM are not configured.")
        return False
    payload = {
        "sender": {"name": settings.email_from_name, "email": settings.email_from.strip()},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html,
        "textContent": text,
    }
    headers = {"api-key": settings.brevo_api_key.strip(), "accept": "application/json"}
    try:
        r = httpx.post(BREVO_URL, json=payload, headers=headers, timeout=15)
    except httpx.HTTPError as exc:
        logger.error("Email not sent: could not reach Brevo (%s).", type(exc).__name__)
        return False
    if r.status_code >= 300:
        # Brevo explains refusals in the body (e.g. sender not verified); it never contains our key.
        logger.error("Email not sent: Brevo answered HTTP %s: %s", r.status_code, r.text[:300])
        return False
    return True
