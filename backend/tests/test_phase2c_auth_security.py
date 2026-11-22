"""Phase 2C: change password + login rate limit (in-memory SQLite, real routers, no network)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import auth as auth_routes
from app.api.routes import users as users_routes
from app.core.login_limiter import LoginLimiter
from app.core.security import verify_password
from app.db.base import Base
from app.db.database import get_db
from app.models.user import User

EMAIL, PASSWORD = "student@example.com", "CorrectPass1"


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[User.__table__])
    Session = sessionmaker(bind=engine)

    def db():
        with Session() as s:
            yield s

    # a fresh limiter per test, with a clock the test controls
    clock = {"now": 1000.0}
    limiter = LoginLimiter(clock=lambda: clock["now"])
    monkeypatch.setattr(auth_routes, "login_limiter", limiter)

    app = FastAPI()
    app.include_router(auth_routes.router)
    app.include_router(users_routes.router)
    app.dependency_overrides[get_db] = db
    c = TestClient(app)
    r = c.post("/auth/register", json={"name": "Student", "email": EMAIL, "password": PASSWORD})
    assert r.status_code == 201
    c.clock, c.Session = clock, Session
    return c


def login(c, password=PASSWORD, email=EMAIL):
    return c.post("/auth/login", json={"email": email, "password": password})


def auth_header(c):
    return {"Authorization": f"Bearer {login(c).json()['access_token']}"}


# ---------------------------------------------------------------- login rate limit

def test_rate_limit_blocks_after_five_failures(client):
    for _ in range(5):
        assert login(client, "wrong-password").status_code == 401
    r = login(client)                                   # even the RIGHT password is refused now
    assert r.status_code == 429
    assert "Too many failed login attempts" in r.json()["detail"]
    assert int(r.headers["Retry-After"]) > 0


def test_block_lifts_after_fifteen_minutes(client):
    for _ in range(5):
        login(client, "wrong-password")
    client.clock["now"] += 15 * 60 + 1
    assert login(client).status_code == 200


def test_successful_login_resets_the_count(client):
    for _ in range(4):
        login(client, "wrong-password")
    assert login(client).status_code == 200            # 4 failures + success -> counter cleared
    for _ in range(4):
        assert login(client, "wrong-password").status_code == 401
    assert login(client).status_code == 200


def test_limit_is_per_email_and_case_insensitive(client):
    for _ in range(5):
        login(client, "wrong-password", email="Student@Example.com")
    assert login(client).status_code == 429             # same email, different case
    assert login(client, email="someone.else@example.com").status_code == 401   # others unaffected


def test_unknown_email_is_limited_the_same_way(client):
    """Same behaviour for registered and unregistered emails, so the limit reveals nothing."""
    for _ in range(5):
        assert login(client, email="nobody@example.com").status_code == 401
    assert login(client, email="nobody@example.com").status_code == 429


def test_limiter_unit_window_slides():
    t = {"now": 0.0}
    lim = LoginLimiter(max_failed=2, window_seconds=10, clock=lambda: t["now"])
    lim.record_failure("a@x.com"); t["now"] = 5
    lim.record_failure("a@x.com")
    assert lim.retry_after("a@x.com") > 0
    t["now"] = 10.5                                     # first failure expired
    assert lim.retry_after("a@x.com") == 0


# ---------------------------------------------------------------- change password

def test_change_password_success(client):
    h = auth_header(client)
    r = client.put("/users/me/password", headers=h,
                   json={"current_password": PASSWORD, "new_password": "BrandNewPass2"})
    assert r.status_code == 204
    assert login(client).status_code == 401                         # old password no longer works
    assert login(client, "BrandNewPass2").status_code == 200
    with client.Session() as s:
        stored = s.query(User).filter_by(email=EMAIL).one().password_hash
    assert stored != "BrandNewPass2" and verify_password("BrandNewPass2", stored)   # bcrypt hash only


def test_change_password_wrong_current_is_400(client):
    r = client.put("/users/me/password", headers=auth_header(client),
                   json={"current_password": "not-it", "new_password": "BrandNewPass2"})
    assert r.status_code == 400 and r.json()["detail"] == "Current password is incorrect."
    assert login(client).status_code == 200                         # unchanged


def test_change_password_validation(client):
    h = auth_header(client)
    too_short = client.put("/users/me/password", headers=h,
                           json={"current_password": PASSWORD, "new_password": "short"})
    same = client.put("/users/me/password", headers=h,
                      json={"current_password": PASSWORD, "new_password": PASSWORD})
    assert too_short.status_code == 422 and same.status_code == 422


def test_change_password_needs_login(client):
    r = client.put("/users/me/password", json={"current_password": PASSWORD, "new_password": "BrandNewPass2"})
    assert r.status_code in (401, 403)
