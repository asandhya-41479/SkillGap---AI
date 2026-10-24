"""Module 6 Step 4: check whether a GitHub repository really contains work for a skill.

Only STRUCTURAL signals in the repository root count: files, folders, declared dependencies and language
bytes. A README mention, the repo name or its topics never verify anything. A skill with no rule stays "linked".
The only network call is _get, so tests replace it and never touch GitHub.
"""
import json
import re
from dataclasses import dataclass

import httpx

from app.models.readiness import VerificationStatus as V
from app.services.skill_normalization import normalize_skill_name

API = "https://api.github.com"
TIMEOUT = httpx.Timeout(10.0)
MIN_LANGUAGE_BYTES = 2000
MAX_FILE_CHARS = 200_000
MANIFESTS = ("requirements.txt", "pyproject.toml", "package.json")
REPO_URL = re.compile(r"^https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100}?)(?:\.git)?/?$")


class GitHubUnavailable(Exception):
    """Network failure, rate limit, revoked token or GitHub error: we simply could not check."""


class RepoNotFound(Exception):
    """Missing, private-and-inaccessible, or not owned by the connected account."""


@dataclass(frozen=True)
class Rule:
    files: tuple[str, ...] = ()
    dirs: tuple[str, ...] = ()
    exts: tuple[str, ...] = ()
    deps: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()


SIGNALS: dict[str, Rule] = {
    "docker": Rule(files=("dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")),
    "kubernetes": Rule(files=("chart.yaml", "kustomization.yaml", "skaffold.yaml"), dirs=("k8s", "kubernetes", "helm", "charts")),
    "fastapi": Rule(deps=("fastapi",)),
    "flask": Rule(deps=("flask",)),
    "django": Rule(deps=("django",)),
    "sqlalchemy": Rule(deps=("sqlalchemy",)),
    "pytest": Rule(deps=("pytest",)),
    "postgresql": Rule(deps=("psycopg2", "psycopg2-binary", "psycopg", "asyncpg", "pg")),
    "sql": Rule(exts=(".sql",), dirs=("migrations", "alembic")),
    "aws": Rule(files=("serverless.yml", "samconfig.toml", "cdk.json"), deps=("boto3", "aws-sdk", "aws-cdk-lib")),
    "terraform": Rule(exts=(".tf",)),
    "react": Rule(deps=("react",)),
    "node.js": Rule(files=("package.json",)),
    "typescript": Rule(files=("tsconfig.json",), languages=("TypeScript",)),
    "python": Rule(languages=("Python",)),
    "javascript": Rule(languages=("JavaScript",)),
    "java": Rule(languages=("Java",)),
    "go": Rule(languages=("Go",)),
    "rust": Rule(languages=("Rust",)),
    "c++": Rule(languages=("C++",)),
    "c#": Rule(languages=("C#",)),
}


@dataclass(frozen=True)
class RepoCheck:
    status: V
    detail: str
    full_name: str


def skill_key(name: str) -> str:
    return normalize_skill_name(name).lower()


def parse_repo_url(url: str) -> tuple[str, str] | None:
    m = REPO_URL.match(url.strip())
    if not m or m.group(2) in (".", ".."):
        return None
    return m.group(1), m.group(2)


def _get(path: str, token: str, raw: bool = False):
    """(status_code, body). 404 -> (404, None). Anything unexpected raises GitHubUnavailable."""
    accept = "application/vnd.github.raw+json" if raw else "application/vnd.github+json"
    try:
        r = httpx.get(API + path, headers={"Authorization": f"Bearer {token}", "Accept": accept}, timeout=TIMEOUT)
        if r.status_code == 404:
            return 404, None
        if r.status_code != 200:
            raise GitHubUnavailable(f"GitHub answered {r.status_code}")
        return 200, (r.text if raw else r.json())
    except (httpx.HTTPError, ValueError) as e:
        raise GitHubUnavailable("GitHub could not be reached") from e


def _pkg(s: str) -> str:
    return re.split(r"[\s\[<>=!~;@(]", s.strip(), maxsplit=1)[0].lower().replace("_", "-")


def _dependency_names(manifest: str, text: str) -> set[str]:
    text = text[:MAX_FILE_CHARS]
    if manifest == "package.json":
        try:
            data = json.loads(text)
        except ValueError:
            return set()
        if not isinstance(data, dict):
            return set()
        return {k.lower() for sec in ("dependencies", "devDependencies") for k in (data.get(sec) or {})}
    if manifest == "requirements.txt":
        lines = (line.split("#")[0].strip() for line in text.splitlines())
        return {_pkg(line) for line in lines if line and not line.startswith("-")}
    return {_pkg(s) for s in re.findall(r"[\"']([^\"'\n]+)[\"']", text)}  # pyproject.toml: quoted requirement strings


def _find_signal(token: str, full: str, rule: Rule) -> str | None:
    """Description of the first structural signal found in the repository root, else None."""
    code, listing = _get(f"/repos/{full}/contents/", token)
    items = listing if code == 200 and isinstance(listing, list) else []
    files = {i["name"].lower(): i["name"] for i in items if i.get("type") == "file" and i.get("name")}
    dirs = {i["name"].lower(): i["name"] for i in items if i.get("type") == "dir" and i.get("name")}
    for f in rule.files:
        if f in files:
            return f"{files[f]} in the repository root"
    for d in rule.dirs:
        if d in dirs:
            return f"folder {dirs[d]}/ in the repository root"
    for e in rule.exts:
        hit = next((n for low, n in files.items() if low.endswith(e)), None)
        if hit:
            return f"{hit} in the repository root"
    if rule.languages:
        code, langs = _get(f"/repos/{full}/languages", token)
        langs = langs if code == 200 and isinstance(langs, dict) else {}
        for lang in rule.languages:
            if isinstance(langs.get(lang), int) and langs[lang] >= MIN_LANGUAGE_BYTES:
                return f"{langs[lang] // 1000 or 1} KB of {lang} code"
    if rule.deps:
        for manifest in MANIFESTS:
            if manifest in files:
                code, text = _get(f"/repos/{full}/contents/{manifest}", token, raw=True)
                hit = _dependency_names(manifest, text or "") & set(rule.deps)
                if hit:
                    return f"dependency {sorted(hit)[0]} declared in {manifest}"
    return None


def check_repo(token: str, username: str, owner: str, repo: str, skill_name: str) -> RepoCheck:
    """Raises RepoNotFound (missing / not the user's) or GitHubUnavailable (could not check)."""
    code, info = _get(f"/repos/{owner}/{repo}", token)
    if code == 404 or not isinstance(info, dict):
        raise RepoNotFound
    if str((info.get("owner") or {}).get("login", "")).lower() != username.lower():
        raise RepoNotFound
    full = info.get("full_name") or f"{owner}/{repo}"
    if info.get("fork"):
        return RepoCheck(V.unverified, "This repository is a fork, so it may not contain your own work.", full)
    rule = SIGNALS.get(skill_key(skill_name))
    if rule is None:
        return RepoCheck(V.linked, "Repository found on your account. No automatic check exists for this skill, "
                                   "so it is linked but not verified.", full)
    found = _find_signal(token, full, rule)
    if found:
        return RepoCheck(V.verified, f"Found {found}.", full)
    return RepoCheck(V.unverified, "Repository found, but nothing in its root (files, folders, dependencies or "
                                   "languages) shows this skill.", full)