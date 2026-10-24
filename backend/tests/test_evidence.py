"""Module 6 Step 4 tests: skill evidence API + GitHub verification (GitHub is faked; no network)."""
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.evidence import router as evidence_router
from app.core import readiness_config as cfg
from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.github_connection import GitHubConnection
from app.models.readiness import ProgressEvidence
from app.models.skill import UserSkill
from app.services import evidence_service, github_evidence as ge
from tests.test_roadmap_api import api, create  # noqa: F401  (api is a pytest fixture)

LOGIN = "vinod"


class FakeGitHub:
    """repos: {'owner/repo': dict(fork=False, root=[names], dirs=[names], langs={}, files={name: text})}"""
    def __init__(self):
        self.repos, self.down, self.calls = {}, False, []

    def __call__(self, path, token, raw=False):
        self.calls.append(path)
        assert token == "tok-secret"
        if self.down:
            raise ge.GitHubUnavailable("down")
        parts = path.strip("/").split("/")
        full = "/".join(parts[1:3])
        r = self.repos.get(full)
        if r is None:
            return 404, None
        rest = parts[3:]
        if not rest:
            return 200, {"full_name": full, "fork": r.get("fork", False), "owner": {"login": full.split("/")[0]}}
        if rest[0] == "languages":
            return 200, r.get("langs", {})
        if rest[0] == "contents":
            if len(rest) == 1:
                return 200, ([{"name": n, "type": "file"} for n in r.get("root", [])]
                             + [{"name": n, "type": "dir"} for n in r.get("dirs", [])])
            return 200, r["files"][rest[1]]
        raise AssertionError(path)


@pytest.fixture()
def ev(api, monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(ge, "_get", fake)
    app = FastAPI()
    app.include_router(evidence_router)
    app.dependency_overrides.update(api.app.dependency_overrides)
    client = TestClient(app)
    with api.Session() as s:
        s.add(GitHubConnection(user_id=api.uid, github_username=LOGIN, github_user_id=1, access_token="tok-secret"))
        s.commit()
    return SimpleNamespace(c=client, gh=fake, api=api, app=app,
                           post=lambda **j: client.post("/evidence", json=j))


def project(skill="FastAPI", url="https://example.com/demo", **kw):
    return dict(skill_name=skill, kind="project_url", url=url, **kw)


def repo(skill="Docker", name="app", owner=LOGIN, **kw):
    return dict(skill_name=skill, kind="github_repo", url=f"https://github.com/{owner}/{name}", **kw)


# ---------- project links ----------
def test_project_url_is_linked_not_verified(ev):
    r = ev.post(**project(note=" my demo "))
    assert r.status_code == 201
    d = r.json()
    assert d["verification_status"] == "linked" and d["strength"] == 0.6 and d["note"] == "my demo"
    assert ev.gh.calls == []                                  # a project link is never fetched


@pytest.mark.parametrize("url", ["http://example.com/x", "https://localhost/x", "https://127.0.0.1/x",
                                 "https://169.254.169.254/latest", "https://user:pw@example.com/x",
                                 "https://example.com:8443/x", "https://intranet/x", "https://foo.internal/x",
                                 "https://[::1]/x", "ftp://example.com/x", "https://exa mple.com/x"])
def test_unsafe_project_urls_rejected(ev, url):
    assert ev.post(**project(url=url)).status_code in (400, 422)


def test_url_is_canonicalised_and_duplicates_409(ev):
    assert ev.post(**project(url="https://Example.COM/demo/")).json()["url"] == "https://example.com/demo"
    assert ev.post(**project(url="https://example.com/demo")).status_code == 409
    assert ev.post(**project(skill="fastapi", url="https://example.com/demo")).status_code == 409   # case-insensitive
    assert ev.post(**project(skill="Docker", url="https://example.com/demo")).status_code == 201     # other skill is fine


def test_alias_skill_name_is_normalised(ev):
    assert ev.post(**project(skill="postgres")).json()["skill_name"] == "PostgreSQL"


def test_limits(ev, monkeypatch):
    monkeypatch.setattr(cfg, "MAX_EVIDENCE_PER_SKILL", 2)
    assert [ev.post(**project(url=f"https://example.com/{i}")).status_code for i in range(3)] == [201, 201, 400]
    monkeypatch.setattr(cfg, "MAX_EVIDENCE_PER_USER", 2)
    assert ev.post(**project(skill="Docker")).status_code == 400


# ---------- GitHub ----------
def test_github_requires_connection(ev):
    with ev.api.Session() as s:
        s.query(GitHubConnection).delete(); s.commit()
    assert ev.post(**repo()).status_code == 400


def test_github_repo_of_another_account_rejected_without_calling_github(ev):
    assert ev.post(**repo(owner="someone-else")).status_code == 400
    assert ev.gh.calls == []


@pytest.mark.parametrize("url", ["https://github.com/vinod", "https://github.com/vinod/app/issues",
                                 "https://gitlab.com/vinod/app", "https://github.com.evil.io/vinod/app"])
def test_bad_github_urls(ev, url):
    assert ev.post(skill_name="Docker", kind="github_repo", url=url).status_code == 400


def test_verified_when_structural_signal_found(ev):
    ev.gh.repos["vinod/app"] = dict(root=["README.md", "Dockerfile"])
    d = ev.post(**repo()).json()
    assert d["verification_status"] == "verified" and d["strength"] == 1.0
    assert d["repo_full_name"] == "vinod/app" and "Dockerfile" in d["verification_detail"] and d["verified_at"]


def test_readme_mention_is_not_proof(ev):
    ev.gh.repos["vinod/app"] = dict(root=["README.md"], files={"README.md": "I use Docker and Kubernetes!"})
    d = ev.post(**repo()).json()
    assert d["verification_status"] == "unverified" and d["strength"] == 0.25
    assert not any("README" in c for c in ev.gh.calls[1:])    # README content is never even fetched


def test_dependency_signal_in_manifest(ev):
    ev.gh.repos["vinod/api"] = dict(root=["requirements.txt"], files={"requirements.txt": "# x\nFastAPI[all]==0.1\nuvicorn\n"})
    assert ev.post(**repo("FastAPI", "api")).json()["verification_status"] == "verified"
    ev.gh.repos["vinod/web"] = dict(root=["package.json"],
                                    files={"package.json": json.dumps({"dependencies": {"react": "^18"}})})
    assert ev.post(**repo("React", "web")).json()["verification_status"] == "verified"
    ev.gh.repos["vinod/lookalike"] = dict(root=["requirements.txt"], files={"requirements.txt": "fastapi-utils\n"})
    assert ev.post(**repo("FastAPI", "lookalike")).json()["verification_status"] == "unverified"


def test_language_signal_needs_enough_code(ev):
    ev.gh.repos["vinod/tiny"] = dict(langs={"Python": 300})
    ev.gh.repos["vinod/big"] = dict(langs={"Python": 40000})
    assert ev.post(**repo("Python", "tiny")).json()["verification_status"] == "unverified"
    assert ev.post(**repo("Python", "big")).json()["verification_status"] == "verified"


def test_directory_signal(ev):
    ev.gh.repos["vinod/ops"] = dict(dirs=["k8s"])
    assert ev.post(**repo("Kubernetes", "ops")).json()["verification_status"] == "verified"


def test_skill_without_rule_stays_linked(ev):
    ev.gh.repos["vinod/app"] = dict(root=["Dockerfile"])
    d = ev.post(**repo("Communication", "app")).json()
    assert d["verification_status"] == "linked" and d["strength"] == 0.6


def test_fork_is_not_verified(ev):
    ev.gh.repos["vinod/app"] = dict(fork=True, root=["Dockerfile"])
    assert ev.post(**repo()).json()["verification_status"] == "unverified"


def test_missing_repo_rejected(ev):
    assert ev.post(**repo(name="nope")).status_code == 400


def test_github_outage_saves_unavailable_then_verify_retries(ev):
    ev.gh.down = True
    d = ev.post(**repo()).json()
    assert d["verification_status"] == "unavailable" and d["strength"] == 0.6 and d["verified_at"] is None
    ev.gh.down = False
    ev.gh.repos["vinod/app"] = dict(root=["Dockerfile"])
    r = ev.c.post(f"/evidence/{d['id']}/verify")
    assert r.status_code == 200 and r.json()["verification_status"] == "verified"


def test_verify_only_for_github(ev):
    pid = ev.post(**project()).json()["id"]
    assert ev.c.post(f"/evidence/{pid}/verify").status_code == 400


def test_token_never_in_responses(ev):
    ev.gh.repos["vinod/app"] = dict(root=["Dockerfile"])
    ev.post(**repo())
    assert "tok-secret" not in ev.c.get("/evidence").text


# ---------- roadmap item link ----------
def test_roadmap_item_link_rules(ev):
    d = create(ev.api)
    docker = next(i for i in d["items"] if i["skill_name"] == "Docker")
    assert ev.post(**project("Docker", roadmap_item_id=docker["id"])).status_code == 201
    assert ev.post(**project("FastAPI", url="https://example.com/2", roadmap_item_id=docker["id"])).status_code == 400
    assert ev.post(**project("Docker", url="https://example.com/3", roadmap_item_id=99999)).status_code == 404
    ev.api.as_user(ev.api.other)
    assert ev.post(**project("Docker", url="https://example.com/4", roadmap_item_id=docker["id"])).status_code == 404


# ---------- list / get / delete / ownership ----------
def test_list_filter_get_delete(ev):
    a = ev.post(**project("FastAPI")).json()
    ev.post(**project("Docker", url="https://example.com/d"))
    assert len(ev.c.get("/evidence").json()) == 2
    assert [e["id"] for e in ev.c.get("/evidence?skill_name=fastapi").json()] == [a["id"]]
    assert ev.c.get(f"/evidence/{a['id']}").json()["id"] == a["id"]
    assert ev.c.delete(f"/evidence/{a['id']}").status_code == 204
    assert ev.c.get(f"/evidence/{a['id']}").status_code == 404
    assert ev.c.delete(f"/evidence/{a['id']}").status_code == 404


def test_other_user_cannot_touch_evidence(ev):
    a = ev.post(**project()).json()
    ev.api.as_user(ev.api.other)
    assert ev.c.get("/evidence").json() == []
    for m, u in [("get", f"/evidence/{a['id']}"), ("delete", f"/evidence/{a['id']}"), ("post", f"/evidence/{a['id']}/verify")]:
        assert getattr(ev.c, m)(u).status_code == 404
    ev.api.as_user(ev.api.uid)
    assert ev.c.get(f"/evidence/{a['id']}").status_code == 200


def test_login_required(ev):
    ev.app.dependency_overrides.pop(get_current_user)
    for m, u in [("get", "/evidence"), ("post", "/evidence"), ("get", "/evidence/1"),
                 ("delete", "/evidence/1"), ("post", "/evidence/1/verify")]:
        assert getattr(ev.c, m)(u).status_code in (401, 403)


def test_adding_evidence_never_changes_a_skill_level(ev):
    from app.models.skill import SkillLevel
    with ev.api.Session() as s:
        s.add(UserSkill(user_id=ev.api.uid, skill_name="Docker", self_assessed_level=SkillLevel.beginner, is_manual=True))
        s.commit()

    def snap():
        with ev.api.Session() as s:
            return [(u.skill_name, u.self_assessed_level, u.updated_at) for u in s.query(UserSkill).all()]
    before = snap()
    ev.gh.repos["vinod/app"] = dict(root=["Dockerfile"])
    assert ev.post(**repo("Docker")).json()["verification_status"] == "verified"
    assert snap() == before and any(n == "Docker" and l == SkillLevel.beginner for n, l, _ in before)


# ---------- strengths for the readiness engine ----------
def test_evidence_strengths_best_wins_and_learning_is_weakest(ev):
    d = create(ev.api)
    docker = next(i for i in d["items"] if i["skill_name"] == "Docker")
    ev.api.client.patch(f"/roadmaps/{d['id']}/items/{docker['id']}", json={"status": "completed"})
    with ev.api.Session() as s:
        assert evidence_service.evidence_strengths(s, ev.api.uid) == {"docker": 0.25}   # completed item only
    ev.post(**project("Docker"))
    ev.gh.repos["vinod/app"] = dict(root=["Dockerfile"])
    ev.post(**repo("Docker"))
    with ev.api.Session() as s:
        assert evidence_service.evidence_strengths(s, ev.api.uid)["docker"] == 1.0
        assert evidence_service.evidence_strengths(s, ev.api.other) == {}