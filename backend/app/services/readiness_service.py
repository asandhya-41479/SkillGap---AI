"""Module 6 Steps 5-7: loads the inputs, runs the pure engine, selects next action,
stores snapshots per (user, job, analysis, day), tracks history, and compares before/after.
"""
import hashlib
import json
import logging
from datetime import date
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core import readiness_config as cfg
from app.models.readiness import ReadinessSnapshot, SnapshotTrigger
from app.models.roadmap import ItemStatus, Roadmap, RoadmapLifecycle
from app.models.skill_gap import AnalysisStatus, MatchClassification, PriorityLevel, SkillGapAnalysis, SkillGapResult
from app.schemas.readiness import HistoryPoint, NextAction, ReadinessComparison, ReadinessHistory, SkillChange
from app.services import readiness_engine as engine
from app.services.evidence_service import evidence_strengths
from app.services.github_evidence import skill_key
from app.services.roadmap.roadmap_service import progress

logger = logging.getLogger(__name__)


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
    raw = json.dumps([key, sorted((k, round(v, 4)) for k, v in strengths.items() if k in {skill_key(r.skill) for r in reqs}),
                      rm.id if rm else None, pct, cfg.FORMULA_VERSION])
    return a, rm, reqs, strengths, pct, out, hashlib.sha256(raw.encode()).hexdigest()


def select_next_action(reqs: list[engine.Req], strengths: dict[str, float], rm: Roadmap | None) -> NextAction | None:
    """Deterministically identifies the highest-leverage next action to improve readiness."""
    if rm and rm.items:
        # 1. In-progress item
        in_prog = next((i for i in rm.items if i.status == ItemStatus.in_progress and i.is_scheduled), None)
        if in_prog:
            alts = [f"Continue {i.skill_name}" for i in rm.items if i.status == ItemStatus.in_progress and i.id != in_prog.id][:2]
            return NextAction(
                kind="roadmap_item",
                title=f"Complete {in_prog.skill_name} task",
                skill_name=in_prog.skill_name,
                item_id=in_prog.id,
                reason_codes=["in_progress", "currently_active"],
                alternatives=alts,
            )

        # 2. Next unblocked scheduled roadmap item
        completed_names = {skill_key(i.skill_name) for i in rm.items if i.status in (ItemStatus.completed, ItemStatus.skipped)}
        unstarted = [i for i in rm.items if i.status == ItemStatus.not_started and i.is_scheduled]
        # Filter items whose prerequisites are satisfied
        ready = [i for i in unstarted if all(skill_key(pr) in completed_names for pr in (i.prerequisites or []))]
        if ready:
            # Sort: high priority first, then order_index
            pri_rank = {"high": 0, "medium": 1, "low": 2, "none": 3}
            ready.sort(key=lambda i: (pri_rank.get(i.priority.value if hasattr(i.priority, "value") else str(i.priority), 3), i.order_index))
            top = ready[0]
            alts = [f"Start learning {i.skill_name}" for i in ready[1:3]]
            return NextAction(
                kind="roadmap_item",
                title=f"Start learning {top.skill_name}",
                skill_name=top.skill_name,
                item_id=top.id,
                reason_codes=["next_scheduled", f"priority_{top.priority}"],
                alternatives=alts,
            )

    # 3. High-priority gap without verified evidence (strength < 0.6)
    gaps_needing_evidence = [
        r for r in reqs
        if r.priority == PriorityLevel.high and strengths.get(skill_key(r.skill), 0.0) < 0.60
    ]
    if gaps_needing_evidence:
        top_gap = gaps_needing_evidence[0]
        alts = [f"Add project for {g.skill}" for g in gaps_needing_evidence[1:3]]
        return NextAction(
            kind="add_evidence",
            title=f"Attach project or repository evidence for {top_gap.skill}",
            skill_name=top_gap.skill,
            reason_codes=["high_priority_gap", "needs_evidence"],
            alternatives=alts,
        )

    # 4. If all high-priority gaps have evidence or strong matches, suggest re-analysis
    if any(r.classification != MatchClassification.strong for r in reqs):
        return NextAction(
            kind="rerun_analysis",
            title="Re-run Skill Gap Analysis to update your readiness score",
            reason_codes=["skills_updated", "reanalysis_recommended"],
        )

    return NextAction(
        kind="roadmap_item",
        title="Review target role requirements and maintain practical project evidence",
        reason_codes=["all_skills_covered"],
    )


def _gemini_feedback_call(prompt: str) -> str:
    from app.services.roadmap.roadmap_llm import _client
    from google.genai import types
    config = types.GenerateContentConfig(temperature=0.3, max_output_tokens=150)
    return _client().models.generate_content(model="gemini-3.6-flash", contents=prompt, config=config).text


def _generate_ai_feedback(score: float | None, label: str | None, metrics: dict, next_act: NextAction | None) -> str:
    """Optional advisory summary. Pure deterministic fallback ensures it never fails."""
    if score is None or not next_act:
        return f"Career Readiness: {label or 'Not enough data'}."

    target_action = next_act.title
    open_high = metrics.get("high_priority_open", 0)
    cov = metrics.get("required_covered", 0)
    tot = metrics.get("required_total", 0)

    # Deterministic fallback text
    fallback = (
        f"Your current Career Readiness Score is {score}/100 ({label}). "
        f"You have covered {cov} of {tot} required skills with {open_high} high-priority gap(s) remaining. "
        f"Recommended next step: {target_action}."
    )

    try:
        prompt = (
            f"Provide a concise, 2-sentence career coaching update for a learner with a readiness score of {score}/100 ({label}). "
            f"Required skills covered: {cov}/{tot}. High-priority open gaps: {open_high}. "
            f"Recommended next action: {target_action}. "
            f"Rules: Do NOT promise hiring, jobs, or timelines. Be realistic, encouraging, and professional. Plain text only."
        )
        text = _gemini_feedback_call(prompt).strip().replace("\n", " ")
        if 20 <= len(text) <= 400:
            return text
    except Exception:
        logger.debug("Gemini readiness feedback fallback used")

    return fallback


def calculate(db: Session, user_id: int, analysis_id: int, trigger=SnapshotTrigger.manual) -> ReadinessSnapshot:
    a, rm, reqs, strengths, pct, out, fp = _run(db, user_id, analysis_id)
    today = date.today()
    snap = (db.query(ReadinessSnapshot).filter(
        ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.job_description_id == a.job_description_id,
        ReadinessSnapshot.analysis_id == a.id, ReadinessSnapshot.snapshot_date == today).first())
    if snap is None:
        snap = ReadinessSnapshot(user_id=user_id, job_description_id=a.job_description_id, analysis_id=a.id,
                                 snapshot_date=today)
        db.add(snap)

    next_act = select_next_action(reqs, strengths, rm)
    next_act_dict = next_act.model_dump() if next_act else None
    feedback = _generate_ai_feedback(out["score"], out["label"], out["metrics"], next_act)

    c = out["components"]
    snap.roadmap_id, snap.score, snap.label = rm.id if rm else None, out["score"], out["label"]
    snap.a_alignment, snap.c_required_coverage, snap.e_evidence = c["alignment"], c["required_coverage"], c["evidence"]
    snap.g_gap_health, snap.p_roadmap, snap.roadmap_included = c["gap_health"], c["roadmap"], c["roadmap"] is not None
    snap.metrics, snap.formula_version, snap.input_fingerprint, snap.trigger = out["metrics"], cfg.FORMULA_VERSION, fp, trigger
    snap.next_action = next_act_dict
    snap.ai_feedback = feedback

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


def latest_for_job(db: Session, user_id: int, job_id: int) -> ReadinessSnapshot:
    snap = (db.query(ReadinessSnapshot).filter(ReadinessSnapshot.user_id == user_id,
                                               ReadinessSnapshot.job_description_id == job_id)
            .order_by(ReadinessSnapshot.snapshot_date.desc(), ReadinessSnapshot.id.desc()).first())
    if snap is None:
        raise HTTPException(404, "No readiness score yet for this job.")
    return snap


def get_history(db: Session, user_id: int, job_id: int) -> ReadinessHistory:
    """Historical timeline of readiness snapshots for a specific target job."""
    snaps = (
        db.query(ReadinessSnapshot)
        .filter(ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.job_description_id == job_id)
        .order_by(ReadinessSnapshot.snapshot_date.asc(), ReadinessSnapshot.id.asc())
        .all()
    )
    points = [
        HistoryPoint(
            snapshot_id=s.id,
            analysis_id=s.analysis_id,
            date=s.snapshot_date,
            score=s.score,
            alignment_pct=(s.metrics or {}).get("alignment_pct"),
            high_priority_open=(s.metrics or {}).get("high_priority_open", 0),
            roadmap_pct=(s.metrics or {}).get("roadmap_pct"),
        )
        for s in snaps
    ]
    return ReadinessHistory(points=points, has_enough_history=len(points) >= 2)


def compare_analyses(db: Session, user_id: int, from_id: int, to_id: int) -> ReadinessComparison:
    """Compares before vs after gap analyses for the same job description."""
    from_a = (
        db.query(SkillGapAnalysis)
        .options(joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement))
        .filter(SkillGapAnalysis.id == from_id, SkillGapAnalysis.user_id == user_id)
        .first()
    )
    to_a = (
        db.query(SkillGapAnalysis)
        .options(joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement))
        .filter(SkillGapAnalysis.id == to_id, SkillGapAnalysis.user_id == user_id)
        .first()
    )
    if from_a is None or to_a is None:
        raise HTTPException(404, "One or both analyses not found")
    if from_a.job_description_id != to_a.job_description_id:
        raise HTTPException(400, "Both analyses must belong to the same job description")

    b_score = from_a.overall_alignment_score
    a_score = to_a.overall_alignment_score
    delta = round(a_score - b_score, 2) if b_score is not None and a_score is not None else None

    strong_b = sum(r.classification == MatchClassification.strong for r in from_a.results)
    strong_a = sum(r.classification == MatchClassification.strong for r in to_a.results)

    high_b = sum(r.priority == PriorityLevel.high for r in from_a.results)
    high_a = sum(r.priority == PriorityLevel.high for r in to_a.results)

    from_map = {r.job_requirement.skill_name.lower(): r.classification.value for r in from_a.results if r.job_requirement}
    to_map = {r.job_requirement.skill_name.lower(): (r.job_requirement.skill_name, r.classification.value) for r in to_a.results if r.job_requirement}

    skill_changes: list[SkillChange] = []
    for k, (name, a_cls) in to_map.items():
        b_cls = from_map.get(k)
        if b_cls and b_cls != a_cls:
            skill_changes.append(SkillChange(skill_name=name, before=b_cls, after=a_cls))

    return ReadinessComparison(
        from_analysis_id=from_id,
        to_analysis_id=to_id,
        alignment_before=b_score,
        alignment_after=a_score,
        alignment_delta_points=delta,
        strong_before=strong_b,
        strong_after=strong_a,
        high_priority_before=high_b,
        high_priority_after=high_a,
        skill_changes=skill_changes,
    )


def to_response(db: Session, user_id: int, snap: ReadinessSnapshot) -> dict:
    """Snapshot + a live recomputation: `breakdown` explains the score and `is_stale` says inputs have changed."""
    _, _, _, _, _, out, fp = _run(db, user_id, snap.analysis_id)
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
