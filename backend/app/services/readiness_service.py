"""Module 6 Steps 5-7: loads the inputs, runs the pure engine, selects next action,
stores snapshots per (user, job, analysis, day), tracks history, and compares before/after.

Gemini is optional and advisory: it only rewords a summary of numbers this module already computed.
It never sees user identity, URLs or evidence, and its text is validated before it is stored.
"""
import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core import readiness_config as cfg
from app.core.skill_gap_config import CLASSIFICATION_CREDIT, IMPORTANCE_WEIGHT
from app.models.readiness import ReadinessSnapshot, SnapshotTrigger
from app.models.roadmap import ItemStatus, Roadmap, RoadmapLifecycle
from app.models.skill_gap import AnalysisStatus, MatchClassification, PriorityLevel, SkillGapAnalysis, SkillGapResult
from app.schemas.readiness import HistoryPoint, NextAction, ReadinessComparison, ReadinessHistory, SkillChange
from app.services import readiness_engine as engine
from app.services.evidence_service import evidence_strengths
from app.services.github_evidence import skill_key
from app.services.roadmap.roadmap_service import progress

logger = logging.getLogger(__name__)

# One small shared pool so a slow Gemini call can be abandoned after the timeout without blocking the request.
_feedback_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="readiness-feedback")
_BANNED = [re.compile(p, re.IGNORECASE) for p in cfg.FEEDBACK_BANNED_PATTERNS]
_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2, "none": 3}


def _val(x) -> str:
    """Enum -> its plain value ('high'), anything else -> str. Avoids 'PriorityLevel.high' on Python 3.11+."""
    return x.value if hasattr(x, "value") else str(x)


# ---------------------------------------------------------------- inputs

def _inputs(db: Session, user_id: int, analysis_id: int):
    a = (db.query(SkillGapAnalysis)
         .options(joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement),
                  joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.matched_user_skill))
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

    results = [r for r in sorted(a.results, key=lambda r: r.job_requirement_id) if r.job_requirement]
    reqs = [engine.Req(r.job_requirement.skill_name, r.job_requirement.importance, r.classification, r.priority)
            for r in results]

    strengths = dict(evidence_strengths(db, user_id))
    # A STRONG semantic match (e.g. requirement "PostgreSQL" matched to user skill "Postgres") may use the
    # evidence of the matched skill. Partial/transferable matches may not: Flask work is not FastAPI proof.
    for r in results:
        if r.classification == MatchClassification.strong and r.matched_user_skill is not None:
            req_k, own_k = skill_key(r.job_requirement.skill_name), skill_key(r.matched_user_skill.skill_name)
            if own_k in strengths:
                strengths[req_k] = max(strengths.get(req_k, 0.0), strengths[own_k])
    return a, rm, reqs, strengths, pct


def _run(db: Session, user_id: int, analysis_id: int):
    a, rm, reqs, strengths, pct = _inputs(db, user_id, analysis_id)
    out = engine.compute(reqs, strengths, pct)
    req_keys = {skill_key(r.skill) for r in reqs}
    key = [[r.skill, _val(r.importance), _val(r.classification), _val(r.priority)] for r in reqs]
    statuses = sorted((i.id, _val(i.status)) for i in rm.items) if rm else []   # next action depends on these
    raw = json.dumps([key, sorted((k, round(v, 4)) for k, v in strengths.items() if k in req_keys),
                      rm.id if rm else None, pct, statuses, cfg.FORMULA_VERSION])
    return a, rm, reqs, strengths, pct, out, hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------- next best action (deterministic)

def select_next_action(reqs: list[engine.Req], strengths: dict[str, float], rm: Roadmap | None) -> NextAction | None:
    """Deterministic order: 1 finish in-progress work, 2 next unblocked roadmap item (high priority first),
    3 attach evidence for an open high-priority skill, 4 re-run the gap analysis."""
    if rm and rm.items:
        scheduled = sorted((i for i in rm.items if i.is_scheduled), key=lambda i: i.order_index)

        # 1. In-progress item (earliest in learning order)
        in_prog = [i for i in scheduled if i.status == ItemStatus.in_progress]
        if in_prog:
            top = in_prog[0]
            return NextAction(
                kind="roadmap_item", title=f"Complete {top.skill_name} task", skill_name=top.skill_name,
                item_id=top.id, reason_codes=["in_progress", "currently_active", f"priority_{_val(top.priority)}"],
                alternatives=[f"Continue {i.skill_name}" for i in in_prog[1:3]],
            )

        # 2. Next unblocked item. A prerequisite is satisfied when it is done/skipped in this roadmap,
        #    or when it is NOT in this roadmap at all (the user already has it, so the planner left it out).
        in_roadmap = {skill_key(i.skill_name) for i in rm.items}
        finished = {skill_key(i.skill_name) for i in rm.items if i.status in (ItemStatus.completed, ItemStatus.skipped)}

        def unblocked(item) -> bool:
            return all(skill_key(p) not in in_roadmap or skill_key(p) in finished for p in (item.prerequisites or []))

        ready = [i for i in scheduled if i.status == ItemStatus.not_started and unblocked(i)]
        if ready:
            ready.sort(key=lambda i: (_PRIORITY_RANK.get(_val(i.priority), 3), i.order_index))
            top = ready[0]
            return NextAction(
                kind="roadmap_item", title=f"Start learning {top.skill_name}", skill_name=top.skill_name,
                item_id=top.id, reason_codes=["next_scheduled", "prerequisites_met", f"priority_{_val(top.priority)}"],
                alternatives=[f"Start learning {i.skill_name}" for i in ready[1:3]],
            )

    # 3. Open high-priority requirement without solid evidence (< 0.60). Most important requirement first.
    needing = [r for r in reqs if r.priority == PriorityLevel.high and strengths.get(skill_key(r.skill), 0.0) < 0.60]
    if needing:
        needing.sort(key=lambda r: -IMPORTANCE_WEIGHT[r.importance])
        top = needing[0]
        return NextAction(
            kind="add_evidence", title=f"Attach project or repository evidence for {top.skill}",
            skill_name=top.skill, reason_codes=["high_priority_gap", "needs_evidence", f"importance_{_val(top.importance)}"],
            alternatives=[f"Add project for {g.skill}" for g in needing[1:3]],
        )

    # 4. Evidence exists but classifications are older than the work: re-run Module 4.
    if any(r.classification != MatchClassification.strong for r in reqs):
        return NextAction(kind="rerun_analysis", title="Re-run Skill Gap Analysis to update your readiness score",
                          reason_codes=["skills_updated", "reanalysis_recommended"])

    return NextAction(kind="roadmap_item",
                      title="Review target role requirements and maintain practical project evidence",
                      reason_codes=["all_skills_covered"])


# ---------------------------------------------------------------- optional Gemini wording

def _gemini_feedback_call(prompt: str) -> str:
    """Tries each configured model in order. Raises if all fail (caller falls back)."""
    from google.genai import types
    from app.services.roadmap.roadmap_llm import _client

    config = types.GenerateContentConfig(temperature=0.3, max_output_tokens=150)
    last: Exception | None = None
    for model in cfg.FEEDBACK_MODELS:
        try:
            text = _client().models.generate_content(model=model, contents=prompt, config=config).text
            if text:
                return text
        except Exception as e:  # try the next model
            last = e
    raise RuntimeError("all feedback models failed") from last


def _clean_feedback(text: str | None) -> str | None:
    """Accept Gemini text only if it is plain, short and makes no hiring/probability claims or links."""
    if not text:
        return None
    text = " ".join(text.split())
    if not (cfg.FEEDBACK_MIN_CHARS <= len(text) <= cfg.FEEDBACK_MAX_CHARS):
        return None
    if any(p.search(text) for p in _BANNED):
        return None
    return text


def _generate_ai_feedback(score: float | None, label: str | None, metrics: dict, next_act: NextAction | None) -> str:
    """Optional advisory summary. The deterministic fallback means this can never fail or hang the request."""
    if score is None or not next_act:
        return f"Career Readiness: {label or cfg.NOT_ENOUGH_DATA}."

    open_high = metrics.get("high_priority_open", 0)
    cov, tot = metrics.get("required_covered", 0), metrics.get("required_total", 0)
    fallback = (
        f"Your current Career Readiness Score is {score}/100 ({label}). "
        f"You have fully covered {cov} of {tot} required skills, with {open_high} high-priority gap(s) remaining. "
        f"Recommended next step: {next_act.title}."
    )
    # Only computed numbers go to Gemini: no name, email, URLs, repo names or evidence notes.
    prompt = (
        f"Write a concise 2-sentence progress update for a learner. Facts (do not change them): "
        f"readiness score {score}/100 ({label}); required skills fully covered {cov}/{tot}; "
        f"high-priority open gaps {open_high}; recommended next action: {next_act.title}. "
        f"Rules: do not mention hiring, jobs offers, chances, probabilities, percentages or timelines; "
        f"do not add new skills or numbers; no links; plain text only."
    )
    try:
        text = _feedback_pool.submit(_gemini_feedback_call, prompt).result(timeout=cfg.FEEDBACK_TIMEOUT_SECONDS)
        cleaned = _clean_feedback(text)
        if cleaned:
            return cleaned
        logger.info("Gemini readiness feedback rejected by validation; using fallback")
    except FutureTimeout:
        logger.warning("Gemini readiness feedback timed out; using fallback")
    except Exception:
        logger.info("Gemini readiness feedback unavailable; using fallback")
    return fallback


# ---------------------------------------------------------------- snapshots

def calculate(db: Session, user_id: int, analysis_id: int, trigger=SnapshotTrigger.manual) -> ReadinessSnapshot:
    a, rm, reqs, strengths, pct, out, fp = _run(db, user_id, analysis_id)
    today = date.today()
    snap = (db.query(ReadinessSnapshot).filter(
        ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.job_description_id == a.job_description_id,
        ReadinessSnapshot.analysis_id == a.id, ReadinessSnapshot.snapshot_date == today).first())
    unchanged = snap is not None and snap.input_fingerprint == fp and bool(snap.ai_feedback)
    if snap is None:
        snap = ReadinessSnapshot(user_id=user_id, job_description_id=a.job_description_id, analysis_id=a.id,
                                 snapshot_date=today)
        db.add(snap)

    next_act = select_next_action(reqs, strengths, rm)
    # Same inputs as today's stored snapshot -> reuse its feedback: no Gemini call, instant response.
    feedback = snap.ai_feedback if unchanged else _generate_ai_feedback(out["score"], out["label"], out["metrics"], next_act)

    c = out["components"]
    snap.roadmap_id, snap.score, snap.label = rm.id if rm else None, out["score"], out["label"]
    snap.a_alignment, snap.c_required_coverage, snap.e_evidence = c["alignment"], c["required_coverage"], c["evidence"]
    snap.g_gap_health, snap.p_roadmap, snap.roadmap_included = c["gap_health"], c["roadmap"], c["roadmap"] is not None
    snap.metrics, snap.formula_version, snap.input_fingerprint, snap.trigger = out["metrics"], cfg.FORMULA_VERSION, fp, trigger
    snap.next_action = next_act.model_dump() if next_act else None
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


# ---------------------------------------------------------------- history & comparison

def get_history(db: Session, user_id: int, job_id: int) -> ReadinessHistory:
    """Real stored snapshots only. Fewer than 2 points -> has_enough_history=False ("Not enough historical data.")."""
    snaps = (db.query(ReadinessSnapshot)
             .filter(ReadinessSnapshot.user_id == user_id, ReadinessSnapshot.job_description_id == job_id)
             .order_by(ReadinessSnapshot.snapshot_date.asc(), ReadinessSnapshot.id.asc()).all())
    points = [
        HistoryPoint(
            snapshot_id=s.id, analysis_id=s.analysis_id, date=s.snapshot_date, score=s.score,
            alignment_pct=(s.metrics or {}).get("alignment_pct"),
            high_priority_open=(s.metrics or {}).get("high_priority_open", 0),
            roadmap_pct=(s.metrics or {}).get("roadmap_pct"),
        )
        for s in snaps
    ]
    return ReadinessHistory(points=points, has_enough_history=len(points) >= 2)


def _alignment_pct(results) -> float | None:
    """Same alignment formula and 0-100 scale as the readiness engine, so every screen shows one number."""
    rs = [r for r in results if r.job_requirement]
    total = sum(IMPORTANCE_WEIGHT[r.job_requirement.importance] for r in rs)
    if not total:
        return None
    got = sum(IMPORTANCE_WEIGHT[r.job_requirement.importance] * CLASSIFICATION_CREDIT[r.classification] for r in rs)
    return round(100 * got / total, 2)


def compare_analyses(db: Session, user_id: int, from_id: int, to_id: int) -> ReadinessComparison:
    """Before vs after for two analyses of the same job. Alignment change is in percentage points."""
    def load(aid: int):
        return (db.query(SkillGapAnalysis)
                .options(joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement))
                .filter(SkillGapAnalysis.id == aid, SkillGapAnalysis.user_id == user_id).first())

    from_a, to_a = load(from_id), load(to_id)
    if from_a is None or to_a is None:
        raise HTTPException(404, "One or both analyses not found")
    if from_a.job_description_id != to_a.job_description_id:
        raise HTTPException(400, "Both analyses must belong to the same job description")

    # Module 4's stored score is the source of truth; recompute (same formula) only if it is missing.
    b_score = from_a.overall_alignment_score if from_a.overall_alignment_score is not None else _alignment_pct(from_a.results)
    a_score = to_a.overall_alignment_score if to_a.overall_alignment_score is not None else _alignment_pct(to_a.results)
    delta = round(a_score - b_score, 2) if b_score is not None and a_score is not None else None

    # An analysis whose per-skill results were removed (job re-analysed) must not be counted as "0 strong".
    before_ok = bool(from_a.results)
    from_map = {r.job_requirement.skill_name.lower(): _val(r.classification) for r in from_a.results if r.job_requirement}
    skill_changes = [
        SkillChange(skill_name=r.job_requirement.skill_name, before=from_map[k], after=_val(r.classification))
        for r in to_a.results if r.job_requirement
        for k in [r.job_requirement.skill_name.lower()]
        if k in from_map and from_map[k] != _val(r.classification)
    ]

    return ReadinessComparison(
        from_analysis_id=from_id, to_analysis_id=to_id,
        alignment_before=b_score, alignment_after=a_score, alignment_delta_points=delta,
        strong_before=sum(r.classification == MatchClassification.strong for r in from_a.results) if before_ok else None,
        strong_after=sum(r.classification == MatchClassification.strong for r in to_a.results),
        high_priority_before=sum(r.priority == PriorityLevel.high for r in from_a.results) if before_ok else None,
        high_priority_after=sum(r.priority == PriorityLevel.high for r in to_a.results),
        skill_changes=skill_changes,
        before_details_unavailable=not before_ok,
    )


# ---------------------------------------------------------------- API response

def _stored_weights(snap: ReadinessSnapshot) -> dict[str, float]:
    comps = {"alignment": snap.a_alignment, "required_coverage": snap.c_required_coverage,
             "evidence": snap.e_evidence, "gap_health": snap.g_gap_health, "roadmap": snap.p_roadmap}
    live = [k for k, v in comps.items() if v is not None]
    wsum = sum(cfg.COMPONENT_WEIGHTS[k] for k in live)
    return {k: round(cfg.COMPONENT_WEIGHTS[k] / wsum, 4) for k in live} if wsum and snap.score is not None else {}


def to_response(db: Session, user_id: int, snap: ReadinessSnapshot) -> dict:
    """Stored snapshot + live check. If its analysis was deleted, the stored score is still shown
    (history must survive) but there is no live breakdown to compare against."""
    out, fp = None, None
    if snap.analysis_id is not None:
        try:
            *_, out, fp = _run(db, user_id, snap.analysis_id)
        except HTTPException:
            out = None   # analysis missing or no longer completed

    fresh = out is not None and fp == snap.input_fingerprint
    return dict(
        id=snap.id, job_description_id=snap.job_description_id, analysis_id=snap.analysis_id,
        roadmap_id=snap.roadmap_id, score=snap.score, label=snap.label, roadmap_included=snap.roadmap_included,
        components=dict(alignment=snap.a_alignment, required_coverage=snap.c_required_coverage, evidence=snap.e_evidence,
                        gap_health=snap.g_gap_health, roadmap=snap.p_roadmap),
        metrics=snap.metrics, formula_version=snap.formula_version, trigger=snap.trigger,
        next_action=snap.next_action, ai_feedback=snap.ai_feedback, snapshot_date=snap.snapshot_date,
        created_at=snap.created_at,
        is_stale=out is not None and not fresh,
        source_available=out is not None,     # False: the analysis was deleted; stored score still shown
        weights=_stored_weights(snap),
        breakdown=out["breakdown"] if out is not None else [],
    )