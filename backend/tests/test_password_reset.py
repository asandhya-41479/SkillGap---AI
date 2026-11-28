"""Forgot / reset password (in-memory SQLite, real routers, email sending replaced by a fake)."""
import re
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import auth as auth_routes
from app.core.login_limiter import LoginLimiter
from app.core.security import verify_password
from app.core.time import utcnow
from app.db.base import Base
from app.db.database import get_db
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services import email_service, password_reset_service

EMAIL, PASSWORD, NEW = "student@example.com", "CorrectPass1", "BrandNewPass2"


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[User.__table__, PasswordResetToken.__table__])
    Session = sessionmaker(bind=engine)

    def db():
        with Session() as s:
            yield s

    sent = []
    monkeypatch.setattr(auth_routes, "SessionLocal", Session)          # background task uses the test DB
    monkeypatch.setattr(password_reset_service, "send_email",
                        lambda to, subject, html, text: sent.append({"to": to, "text": text}) or True)
    monkeypatch.setattr(password_reset_service, "reset_request_limiter", password_reset_service.ResetRequestLimiter())
    limiter = LoginLimiter()
    monkeypatch.setattr(auth_routes, "login_limiter", limiter)
    monkeypatch.setattr(password_reset_service, "login_limiter", limiter)

    app = FastAPI()
    app.include_router(auth_routes.router)
    app.dependency_overrides[get_db] = db
    c = TestClient(app)
    assert c.post("/auth/register", json={"name": "Student", "email": EMAIL, "password": PASSWORD}).status_code == 201
    c.sent, c.Session, c.limiter = sent, Session, limiter
    return c


def token_from(mail) -> str:
    return re.search(r"token=([A-Za-z0-9_\-]+)", mail["text"]).group(1)


def forgot(c, email=EMAIL):
    return c.post("/auth/forgot-password", json={"email": email})


def reset(c, token, password=NEW):
    return c.post("/auth/reset-password", json={"token": token, "new_password": password})


def login(c, password):
    return c.post("/auth/login", json={"email": EMAIL, "password": password})


# ---------------------------------------------------------------- request a link

def test_forgot_sends_one_email_with_a_link(client):
    r = forgot(client)
    assert r.status_code == 202
    assert "If an account exists" in r.json()["detail"]
    assert len(client.sent) == 1 and client.sent[0]["to"] == EMAIL
    assert "/reset-password?token=" in client.sent[0]["text"]


def test_unknown_email_gets_the_same_answer_and_no_email(client):
    known, unknown = forgot(client), forgot(client, "nobody@example.com")
    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    assert [m["to"] for m in client.sent] == [EMAIL]


def test_email_letter_case_does_not_matter(client):
    assert forgot(client, EMAIL.upper()).status_code == 202
    assert [m["to"] for m in client.sent] == [EMAIL]


def test_only_a_hash_of_the_token_is_stored(client):
    forgot(client)
    token = token_from(client.sent[0])
    with client.Session() as s:
        row = s.query(PasswordResetToken).one()
        assert row.token_hash != token and len(row.token_hash) == 64


def test_request_limit_three_per_hour(client):
    for _ in range(5):
        assert forgot(client).status_code == 202            # the answer never changes...
    assert len(client.sent) == 3                            # ...but only 3 emails go out


# ---------------------------------------------------------------- use the link

def test_reset_changes_the_password(client):
    forgot(client)
    assert reset(client, token_from(client.sent[0])).status_code == 204
    assert login(client, PASSWORD).status_code == 401
    assert login(client, NEW).status_code == 200


def test_link_works_only_once(client):
    forgot(client)
    token = token_from(client.sent[0])
    assert reset(client, token).status_code == 204
    r = reset(client, token, "AnotherPass3")
    assert r.status_code == 400 and "invalid or has expired" in r.json()["detail"]


def test_expired_link_is_refused(client):
    forgot(client)
    token = token_from(client.sent[0])
    with client.Session() as s:
        row = s.query(PasswordResetToken).one()
        row.expires_at = utcnow() - timedelta(seconds=1)
        s.commit()
    assert reset(client, token).status_code == 400
    assert login(client, PASSWORD).status_code == 200      # password unchanged


def test_new_request_cancels_the_older_link(client):
    forgot(client)
    forgot(client)
    first, second = token_from(client.sent[0]), token_from(client.sent[1])
    assert reset(client, first).status_code == 400
    assert reset(client, second).status_code == 204


def test_made_up_token_is_refused(client):
    assert reset(client, "x" * 43).status_code == 400


def test_new_password_rules_apply(client):
    forgot(client)
    assert reset(client, token_from(client.sent[0]), "short").status_code == 422


def test_reset_clears_the_login_lock(client):
    for _ in range(5):
        login(client, "wrong-password")
    assert login(client, PASSWORD).status_code == 429
    forgot(client)
    assert reset(client, token_from(client.sent[0])).status_code == 204
    assert login(client, NEW).status_code == 200


# ---------------------------------------------------------------- email sender

def test_email_is_skipped_when_not_configured(monkeypatch):
    monkeypatch.setattr(email_service.settings, "brevo_api_key", "")
    monkeypatch.setattr(email_service.settings, "email_from", "")
    called = []
    monkeypatch.setattr(email_service.httpx, "post", lambda *a, **k: called.append(1))
    assert email_service.send_email("a@example.com", "s", "<p>h</p>", "t") is False
    assert called == []


def test_email_uses_brevo_https_api(monkeypatch):
    monkeypatch.setattr(email_service.settings, "brevo_api_key", "key-123")
    monkeypatch.setattr(email_service.settings, "email_from", "sender@example.com")
    seen = {}

    class Resp:
        status_code, text = 201, "{}"

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, json=json, headers=headers)
        return Resp()

    monkeypatch.setattr(email_service.httpx, "post", fake_post)
    assert email_service.send_email("a@example.com", "Subject", "<p>h</p>", "t") is True
    assert seen["url"].startswith("https://api.brevo.com/")
    assert seen["headers"]["api-key"] == "key-123"
    assert seen["json"]["to"] == [{"email": "a@example.com"}]


def test_brevo_refusal_returns_false(monkeypatch):
    monkeypatch.setattr(email_service.settings, "brevo_api_key", "key-123")
    monkeypatch.setattr(email_service.settings, "email_from", "sender@example.com")

    class Resp:
        status_code, text = 400, '{"message":"sender not valid"}'

    monkeypatch.setattr(email_service.httpx, "post", lambda *a, **k: Resp())
    assert email_service.send_email("a@example.com", "s", "<p>h</p>", "t") is False


def test_email_escapes_the_name():
    _, body, _ = password_reset_service.build_email("<script>x</script>", "https://site/reset-password?token=abc")
    assert "<script>" not in body and "&lt;script&gt;" in body
