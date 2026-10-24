"""Module 6 Step 4: skill evidence (project links and GitHub repositories).

Evidence only ever feeds the readiness score as "demonstrated" strength. It never edits UserSkill or any
proficiency level. Project links are validated but never fetched (no SSRF). GitHub repos are checked with
the user's own stored token, which never leaves the backend.
"""
import ipaddress
from datetime import datetime
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import readiness_config as cfg
from app.models.github_connection import GitHubConnection
from app.models.readiness import EvidenceKind, ProgressEvidence, VerificationStatus as V
from app.models.roadmap import ItemStatus, Roadmap, RoadmapItem
from app.schemas.readiness import EvidenceCreate
from app.services import github_evidence as ge
from app.services.skill_normalization import normalize_skill_name

STATUS_TEXT = {
    V.verified: "Verified: the repository is yours and contains a structural signal for this skill.",
    V.linked: "Linked, not verified: the link was accepted but its content was not checked.",
    V.unverified: "Checked: no signal for this skill was found in the repository.",
    V.unavailable: "GitHub could not be reached, so this was not checked. Use verify to retry.",
}


def strength(kind: EvidenceKind, status: V) -> float:
    return cfg.EVIDENCE_STRENGTH.get((kind, status), 0.0)


def to_response(ev: ProgressEvidence, detail: str | None = None) -> dict:
    return {
        "id": ev.id, "skill_name": ev.skill_name, "kind": ev.kind, "url": ev.url,
        "repo_full_name": ev.repo_full_name, "verification_status": ev.verification_status,
        "verified_at": ev.verified_at, "note": ev.note, "roadmap_item_id": ev.roadmap_item_id,
        "created_at": ev.created_at, "strength": strength(ev.kind, ev.verification_status),
        "verification_detail": detail or STATUS_TEXT[ev.verification_status],
    }


def _clean_project_url(url: str) -> str:
    p = urlparse(url)
    host = (p.hostname or "").lower()
    bad = (
        p.scheme != "https" or not host or p.username or p.password or "." not in host
        or host == "localhost" or host.endswith((".local", ".internal", ".localhost"))
        or p.port not in (None, 443)
    )
    if not bad:
        try:
            ipaddress.ip_address(host)
            bad = True          # raw IP addresses are refused (private ranges, metadata endpoints)
        except ValueError:
            pass
    if bad:
        raise HTTPException(400, "Enter a public https:// link with a normal domain name.")
    return f"https://{host}{p.path.rstrip('/') if p.path != '/' else ''}" + (f"?{p.query}" if p.query else "")


def _own_item(db: Session, user_id: int, item_id: int, skill_name: str) -> RoadmapItem:
    item = (db.query(RoadmapItem).join(Roadmap, Roadmap.id == RoadmapItem.roadmap_id)
            .filter(RoadmapItem.id == item_id, Roadmap.user_id == user_id).first())
    if item is None:
        raise HTTPException(404, "Roadmap item not found")
    if ge.skill_key(item.skill_name) != ge.skill_key(skill_name):
        raise HTTPException(400, "That roadmap item is for a different skill.")
    return item


def _connection(db: Session, user_id: int) -> GitHubConnection:
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == user_id).first()
    if conn is None:
        raise HTTPException(400, "Connect your GitHub account before adding a GitHub repository.")
    return conn


def _run_check(conn: GitHubConnection, owner: str, repo: str, skill: str):
    try:
        return ge.check_repo(conn.access_token, conn.github_username, owner, repo, skill)
    except ge.RepoNotFound:
        raise HTTPException(400, "Repository not found on your connected GitHub account.")
    except ge.GitHubUnavailable:
        return None


def add_evidence(db: Session, user_id: int, data: EvidenceCreate) -> tuple[ProgressEvidence, str | None]:
    skill = normalize_skill_name(data.skill_name).strip()
    if not skill:
        raise HTTPException(400, "Skill name is required.")
    if data.roadmap_item_id is not None:
        _own_item(db, user_id, data.roadmap_item_id, skill)

    mine = db.query(ProgressEvidence).filter(ProgressEvidence.user_id == user_id)
    if mine.count() >= cfg.MAX_EVIDENCE_PER_USER:
        raise HTTPException(400, f"You can store at most {cfg.MAX_EVIDENCE_PER_USER} evidence items.")
    if mine.filter(func.lower(ProgressEvidence.skill_name) == skill.lower()).count() >= cfg.MAX_EVIDENCE_PER_SKILL:
        raise HTTPException(400, f"At most {cfg.MAX_EVIDENCE_PER_SKILL} evidence items per skill.")

    detail = None
    repo_full = None
    verified_at = None
    if data.kind == EvidenceKind.github_repo:
        parsed = ge.parse_repo_url(data.url)
        if parsed is None:
            raise HTTPException(400, "Use a repository link like https://github.com/<you>/<repo>.")
        owner, repo = parsed
        conn = _connection(db, user_id)
        if owner.lower() != conn.github_username.lower():
            raise HTTPException(400, "That repository belongs to a different GitHub account than the one you connected.")
        url = f"https://github.com/{owner}/{repo}"
        res = _run_check(conn, owner, repo, skill)
        if res is None:
            status, detail, repo_full = V.unavailable, None, f"{owner}/{repo}"
        else:
            status, detail, repo_full, verified_at = res.status, res.detail, res.full_name, datetime.utcnow()
    else:
        url = _clean_project_url(data.url)
        status = V.linked

    if mine.filter(func.lower(ProgressEvidence.skill_name) == skill.lower(), ProgressEvidence.url == url).first():
        raise HTTPException(409, "You already added this link for this skill.")

    ev = ProgressEvidence(
        user_id=user_id, skill_name=skill, roadmap_item_id=data.roadmap_item_id, kind=data.kind, url=url,
        repo_full_name=repo_full, verification_status=status, verified_at=verified_at,
        note=(data.note or "").strip() or None,
    )
    db.add(ev)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You already added this link for this skill.")
    db.refresh(ev)
    return ev, detail


def get_evidence(db: Session, user_id: int, evidence_id: int) -> ProgressEvidence:
    ev = db.query(ProgressEvidence).filter(ProgressEvidence.id == evidence_id,
                                           ProgressEvidence.user_id == user_id).first()
    if ev is None:
        raise HTTPException(404, "Evidence not found")
    return ev


def list_evidence(db: Session, user_id: int, skill_name: str | None = None) -> list[ProgressEvidence]:
    q = db.query(ProgressEvidence).filter(ProgressEvidence.user_id == user_id)
    if skill_name:
        q = q.filter(func.lower(ProgressEvidence.skill_name) == normalize_skill_name(skill_name).strip().lower())
    return q.order_by(ProgressEvidence.created_at.desc(), ProgressEvidence.id.desc()).all()


def delete_evidence(db: Session, user_id: int, evidence_id: int) -> None:
    db.delete(get_evidence(db, user_id, evidence_id))
    db.commit()


def reverify(db: Session, user_id: int, evidence_id: int) -> tuple[ProgressEvidence, str | None]:
    ev = get_evidence(db, user_id, evidence_id)
    if ev.kind != EvidenceKind.github_repo:
        raise HTTPException(400, "Only GitHub repositories can be verified.")
    conn = _connection(db, user_id)
    owner, repo = ev.repo_full_name.split("/", 1) if ev.repo_full_name else ge.parse_repo_url(ev.url)
    res = _run_check(conn, owner, repo, ev.skill_name)
    if res is None:
        ev.verification_status, detail = V.unavailable, None
    else:
        ev.verification_status, ev.verified_at, detail = res.status, datetime.utcnow(), res.detail
    db.commit()
    db.refresh(ev)
    return ev, detail


def evidence_strengths(db: Session, user_id: int) -> dict[str, float]:
    """{lower-case canonical skill: 0-1}. Best evidence row wins; a completed roadmap item gives learning
    strength only. Used by the readiness engine (Step 5). Never touches UserSkill."""
    out: dict[str, float] = {}
    done = (db.query(RoadmapItem.skill_name).join(Roadmap, Roadmap.id == RoadmapItem.roadmap_id)
            .filter(Roadmap.user_id == user_id, RoadmapItem.status == ItemStatus.completed).all())
    for (name,) in done:
        k = ge.skill_key(name)
        out[k] = max(out.get(k, 0.0), cfg.LEARNING_STRENGTH)
    for ev in list_evidence(db, user_id):
        k = ge.skill_key(ev.skill_name)
        out[k] = max(out.get(k, 0.0), strength(ev.kind, ev.verification_status))
    return out