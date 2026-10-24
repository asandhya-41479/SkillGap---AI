"""Module 6 Step 5: loads the inputs, runs the pure engine, stores one snapshot per (user, job, analysis, day)."""
import hashlib
import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core import readiness_config as cfg
from app.models.readiness import ReadinessSnapshot, SnapshotTrigger
from app.models.roadmap import Roadmap, RoadmapLifecycle
from app.models.skill_gap import AnalysisStatus, SkillGapAnalysis, SkillGapResult
from app.services import readiness_engine as engine
from app.services.evidence_service import evidence_strengths
from app.services.github_evidence import skill_key
from app.services.roadmap.roadmap_service import progress


def _inputs(db: Session, user_id: int, analysis_id: int):
    a = (db.query(SkillGapAnalysis)
         .options(joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement))
         .filter(SkillGapAnalysis.id == analysis_id, SkillGapAnalysis.user_id == user_id).first())
    if a is None:
        raise HTTPException(404, "Analysis not found")
    if a.status != AnalysisStatus.completed:
        raise HTTPException(400, "This gap analysis did not complete. Re-run it first.")
    rm = (db.query(Roadmap).filter(Roadmap.user_id == user_id, Roadmap.analysis_id == analysis_id,
                                   Roadmap.lifecycle == RoadmapLifecycle.active)
          .order_by(Roadmap.created_at.desc(), Roadmap.id.desc()).first())
    pct = None
    if rm is not None:
        p = progress(rm)
        pct = p.percent_complete if p.total_items else None   # a roadmap with nothing to do says nothing
    reqs = [engine.Req(r.job_requirement.skill_name, r.job_requirement.importance, r.classification, r.priority)
            for r in sorted(a.results, key=lambda r: r.job_requirement_id)]
    return a, rm, reqs, evidence_strengths(db, user_id), pct


def _run(db: Session, user_id: int, analysis_id: int):
    a, rm, reqs, strengths, pct = _inputs(db, user_id, analysis_id)
    out = engine.compute(reqs, strengths, pct)
    key = [[r.skill, r.importance.value, r.classification.value, r.priority.value] for r in reqs]
    raw = json.dumps([key, sorted((k, round(v, 4)) for k, v in strengths.items() if k in {skill_key(r.skill) for r in reqs}), rm.id if rm else None, pct,
                      cfg.FORMULA_VERSION])
    return a, rm, out, hashlib.sha256(raw.encode()).hexdigest()


def calculate(db: Session, user_id: int, analysis_id: int, trigger=SnapshotTrigger.manual) -> ReadinessSnapshot:
    a, rm, out, fp = _run(db, user_id, analysis_id)
    today = date.today()
    snap = (db.query(ReadinessSnapshot).filter(
        ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.job_description_id == a.job_description_id,
        ReadinessSnapshot.analysis_id == a.id, ReadinessSnapshot.snapshot_date == today).first())
    if snap is None:
        snap = ReadinessSnapshot(user_id=user_id, job_description_id=a.job_description_id, analysis_id=a.id,
                                 snapshot_date=today)
        db.add(snap)
    c = out["components"]
    snap.roadmap_id, snap.score, snap.label = rm.id if rm else None, out["score"], out["label"]
    snap.a_alignment, snap.c_required_coverage, snap.e_evidence = c["alignment"], c["required_coverage"], c["evidence"]
    snap.g_gap_health, snap.p_roadmap, snap.roadmap_included = c["gap_health"], c["roadmap"], c["roadmap"] is not None
    snap.metrics, snap.formula_version, snap.input_fingerprint, snap.trigger = out["metrics"], cfg.FORMULA_VERSION, fp, trigger
    db.commit()
    db.refresh(snap)
    return snap


def latest(db: Session, user_id: int, analysis_id: int) -> ReadinessSnapshot:
    snap = (db.query(ReadinessSnapshot).filter(ReadinessSnapshot.user_id == user_id,
                                               ReadinessSnapshot.analysis_id == analysis_id)
            .order_by(ReadinessSnapshot.snapshot_date.desc(), ReadinessSnapshot.id.desc()).first())
    if snap is None:
        raise HTTPException(404, "No readiness score yet. Calculate it first.")
    return snap


def to_response(db: Session, user_id: int, snap: ReadinessSnapshot) -> dict:
    """Snapshot + a live recomputation: `breakdown` explains the score and `is_stale` says inputs have changed."""
    _, _, out, fp = _run(db, user_id, snap.analysis_id)
    return dict(
        id=snap.id, job_description_id=snap.job_description_id, analysis_id=snap.analysis_id,
        roadmap_id=snap.roadmap_id, score=snap.score, label=snap.label, roadmap_included=snap.roadmap_included,
        components=dict(alignment=snap.a_alignment, required_coverage=snap.c_required_coverage, evidence=snap.e_evidence,
                        gap_health=snap.g_gap_health, roadmap=snap.p_roadmap),
        metrics=snap.metrics, formula_version=snap.formula_version, trigger=snap.trigger,
        next_action=snap.next_action, ai_feedback=snap.ai_feedback, snapshot_date=snap.snapshot_date,
        created_at=snap.created_at, is_stale=fp != snap.input_fingerprint,
        weights=out["weights"] if fp == snap.input_fingerprint else {}, breakdown=out["breakdown"],
    )