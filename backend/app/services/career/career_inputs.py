"""Module 7 adapter: the ONLY place Module 7 reads Modules 3-6. Read-only; it never writes their tables.

It reuses Module 6's own loader (readiness_service._run) so Career Readiness and Career Actions are always
computed from exactly the same verified inputs: the Module 4 analysis (ownership + completed checks included),
the active Module 5 roadmap, Module 6 evidence strengths and the live readiness score.
"""
from sqlalchemy.orm import Session

from app.models.career import ActionPriority, InterviewPrepItem, PrepStatus
from app.models.readiness import ProgressEvidence, ReadinessSnapshot
from app.models.roadmap import RoadmapItem
from app.models.skill import SkillEvidence, UserSkill
from app.schemas.career import CareerInputs, EvidenceRef, ReadinessInput, SkillInput
from app.services import readiness_service
from app.services.evidence_service import strength as evidence_strength
from app.services.github_evidence import SIGNALS, skill_key
from app.core import readiness_config


def _v(x):
    return x.value if hasattr(x, "value") else (str(x) if x is not None else None)


def _evidence_refs(db: Session, user_id: int) -> dict[str, list[EvidenceRef]]:
    """skill key -> evidence the user already has (for display + evidence gaps). Strength comes from Module 6."""
    out: dict[str, list[EvidenceRef]] = {}
    add = lambda name, ref: out.setdefault(skill_key(name), []).append(ref)  # noqa: E731

    for ev in db.query(ProgressEvidence).filter(ProgressEvidence.user_id == user_id).all():
        add(ev.skill_name, EvidenceRef(source="progress_evidence", kind=_v(ev.kind), url=ev.url,
                                       status=_v(ev.verification_status),
                                       strength=evidence_strength(ev.kind, ev.verification_status)))
    rows = (db.query(UserSkill.skill_name, SkillEvidence.detected_via, SkillEvidence.repo_url)
            .join(SkillEvidence, SkillEvidence.user_skill_id == UserSkill.id)
            .filter(UserSkill.user_id == user_id).all())
    for name, via, url in rows:
        via = _v(via)
        add(name, EvidenceRef(source="github_detected", kind=via, url=url,
                              strength=readiness_config.MODULE2_EVIDENCE_STRENGTH.get(via, 0.0)))
    return out


def _hint(rule) -> str:
    """Plain-English description of a Module 6 SIGNALS rule (what the GitHub check looks for)."""
    parts = []
    if rule.files:
        parts.append(" or ".join(rule.files) + " in the repository root")
    if rule.dirs:
        parts.append("a " + " / ".join(f"{d}/" for d in rule.dirs) + " folder")
    if rule.exts:
        parts.append(" or ".join(f"*{e}" for e in rule.exts) + " files in the root")
    if rule.deps:
        parts.append(" or ".join(rule.deps) + " declared in requirements.txt, pyproject.toml or package.json")
    if rule.languages:
        parts.append(" or ".join(rule.languages) + " code detected by GitHub")
    return "; or ".join(parts)


def _interview_prep_pct(db: Session, user_id: int, job_id: int) -> float | None:
    """Q for career status: % of active HIGH-priority prep topics marked prepared. None until Step 6 creates them."""
    items = (db.query(InterviewPrepItem.status)
             .filter(InterviewPrepItem.user_id == user_id, InterviewPrepItem.job_description_id == job_id,
                     InterviewPrepItem.is_active.is_(True), InterviewPrepItem.priority == ActionPriority.HIGH).all())
    if not items:
        return None
    return round(100 * sum(s == PrepStatus.PREPARED for (s,) in items) / len(items), 1)


def build(db: Session, user_id: int, analysis_id: int) -> CareerInputs:
    """Raises 404 (analysis not found / not owned) or 400 (analysis failed) exactly like Module 6."""
    a, rm, _reqs, strengths, pct, out, fingerprint = readiness_service._run(db, user_id, analysis_id)

    items: dict[str, RoadmapItem] = {skill_key(i.skill_name): i for i in (rm.items if rm else [])}
    refs = _evidence_refs(db, user_id)

    # Two requirement names can normalize to one skill ("Postgres" / "PostgreSQL"): keep the most important.
    rank = {"required": 0, "preferred": 1, "optional": 2}
    results = sorted((r for r in a.results if r.job_requirement is not None),
                     key=lambda r: (rank.get(_v(r.job_requirement.importance), 3), r.job_requirement_id))
    skills, seen = [], set()
    for r in results:
        req = r.job_requirement
        k = skill_key(req.skill_name)
        if k in seen:
            continue
        seen.add(k)
        item = items.get(k)
        skill_refs = list(refs.get(k, []))
        if item is not None and _v(item.status) == "completed":
            skill_refs.append(EvidenceRef(source="roadmap", kind="completed_item",
                                          strength=readiness_config.LEARNING_STRENGTH))
        skills.append(SkillInput(
            name=req.skill_name, key=k, category=_v(req.category) or "other",
            importance=_v(req.importance), classification=_v(r.classification), m4_priority=_v(r.priority),
            evidence_adjusted=bool(r.evidence_adjusted), gap_result_id=r.id, job_requirement_id=req.id,
            roadmap_item_id=item.id if item else None,
            roadmap_status=_v(item.status) if item else None,
            practical_done=bool(item.practical_done) if item else False,
            prerequisites=[skill_key(p) for p in (item.prerequisites or [])] if item else [],
            evidence_strength=min(1.0, max(0.0, strengths.get(k, 0.0))),
            evidence=skill_refs,
        ))

    snap = (db.query(ReadinessSnapshot.id)
            .filter(ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.analysis_id == a.id)
            .order_by(ReadinessSnapshot.snapshot_date.desc(), ReadinessSnapshot.id.desc()).first())

    return CareerInputs(
        user_id=user_id, analysis_id=a.id, job_description_id=a.job_description_id,
        target_role=(a.job.target_role if a.job else None) or "Target role",
        readiness=ReadinessInput(score=out["score"], label=out["label"], snapshot_id=snap[0] if snap else None,
                                 components=out["components"]),
        roadmap_id=rm.id if rm else None, roadmap_pct=pct,
        interview_prep_pct=_interview_prep_pct(db, user_id, a.job_description_id),
        verifiable_skills=sorted(SIGNALS.keys()),
        verification_hints={k: _hint(r) for k, r in SIGNALS.items()},
        skills=skills, fingerprint=fingerprint,
    )
