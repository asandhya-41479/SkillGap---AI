"""Phase 2A: Swagger sections/summaries and the global error handler (documentation + safety net only)."""
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.errors import DATABASE_MESSAGE, GENERIC_MESSAGE, register_error_handlers
from app.core.openapi import SUMMARIES, TAGS
from app.main import app

EXPECTED_SECTIONS = {"AUTH", "USERS", "SKILLS", "JOBS", "SKILL GAP ANALYSIS", "GITHUB", "ROADMAP", "PROGRESS", "CAREER"}


def test_swagger_has_the_named_sections():
    schema = app.openapi()
    names = {t["name"] for t in schema["tags"]}
    assert EXPECTED_SECTIONS <= names
    used = {tag for path in schema["paths"].values() for op in path.values() for tag in op.get("tags", [])}
    assert EXPECTED_SECTIONS <= used
    assert all(t.get("description") for t in TAGS)


def _operations():
    """Every (METHOD, path) -> operation in the real Swagger output (works on any FastAPI version)."""
    schema = app.openapi()
    return {(m.upper(), path): op for path, ops in schema["paths"].items() for m, op in ops.items()}


def test_every_endpoint_has_its_summary_and_a_section():
    ops = _operations()
    assert len(ops) >= 55                              # all module routers are really included
    for key, op in ops.items():
        assert key in SUMMARIES, f"missing summary: {key}"
        assert op.get("summary") == SUMMARIES[key], f"summary not applied: {key}"
        assert op.get("tags"), f"missing section: {key}"


def test_no_summary_points_at_a_route_that_does_not_exist():
    assert set(SUMMARIES) <= set(_operations())


def test_urls_unchanged():
    paths = {path for _, path in _operations()}
    for p in ("/auth/login", "/users/me", "/skills", "/jobs/{job_id}/analyze", "/gap-analysis/{job_id}",
              "/roadmaps", "/readiness/{analysis_id}", "/evidence", "/career/{analysis_id}/plan", "/health"):
        assert p in paths


def _probe_app():
    probe = FastAPI()
    register_error_handlers(probe)

    @probe.get("/boom")
    def boom():
        raise RuntimeError("secret token=abc123 at C:\\Users\\someone\\file.py")

    @probe.get("/db")
    def db():
        raise OperationalError("SELECT password FROM users", {}, Exception("connection refused"))

    @probe.get("/missing")
    def missing():
        raise HTTPException(404, "Job description not found.")

    return TestClient(probe, raise_server_exceptions=False)


def test_unexpected_error_is_generic_and_leaks_nothing():
    r = _probe_app().get("/boom")
    assert r.status_code == 500 and r.json() == {"detail": GENERIC_MESSAGE}
    assert "secret" not in r.text and "Users" not in r.text and "RuntimeError" not in r.text


def test_database_error_is_generic_and_leaks_nothing():
    r = _probe_app().get("/db")
    assert r.status_code == 500 and r.json() == {"detail": DATABASE_MESSAGE}
    assert "SELECT" not in r.text and "password" not in r.text


def test_normal_http_errors_are_unchanged():
    r = _probe_app().get("/missing")
    assert r.status_code == 404 and r.json() == {"detail": "Job description not found."}
