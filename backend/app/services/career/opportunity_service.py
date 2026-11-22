"""Module 7 Step 7: opportunity matching service (real data only, deterministic, no Gemini).

Sources:
  SAVED_JOB      the user's own Module 3 job descriptions. Computed live from the latest completed Module 4
                 analysis (no duplicate storage); jobs without an analysis are listed as needs_analysis.
  USER_PROVIDED  a job description the user pastes. Skills are found in code (opportunity_matcher), classified
                 with Module 4's own find_best_match, scored with Module 4's own formula and stored as history
                 (hash + extracted requirements only, never the raw text).
  JOB_API        no external job-data source is configured: the API says so and nothing is generated.
"""

from app.core.time import utcnow

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.career import CareerAction, OpportunityMatch, OpportunitySource
from app.models.job import JobDescription, JobRequirement
from app.models.skill import UserSkill
from app.models.skill_gap import AnalysisStatus, SkillGapAnalysis, SkillGapResult
from app.schemas.career import OpportunityMatchRequest
from app.services.career import opportunity_matcher as om
from app.services.github_evidence import skill_key
from app.services.skill_matching_service import find_best_match
from app.services.skill_normalization import ALIASES

JOB_API_CONFIGURED = False
NO_SOURCE_MESSAGE = ("Live job listings require a connected job-data source. "
                     "You can compare your saved job descriptions or paste a real one.")
MAX_HISTORY = 50


def _v(x):
    return x.value if hasattr(x, "value") else x


def _classify(name: str, category: str, user_skills: list[UserSkill]) -> str:
    """Module 4 matching (normalization, exact match, embeddings, false friends, ecosystem pairs)."""
    return _v(find_best_match(name, category, user_skills).classification)


def _action_keys(db: Session, user_id: int, skills: list[str], job_id: int | None = None) -> list[str]:
    """The user's active career actions that work on these skills (same job first)."""
    wanted = {skill_key(s) for s in skills}
    q = db.query(CareerAction).filter(CareerAction.user_id == user_id, CareerAction.is_active.is_(True))
    rows = sorted(q.all(), key=lambda a: (a.job_description_id != job_id, a.rank))
    keys = []
    for a in rows:
        covered = {code.split(":", 1)[1] for code in (a.reason_codes or []) if code.startswith("COVERS:")}
        covered = {k for c in covered for k in c.split(",")}
        if (a.skill_name and skill_key(a.skill_name) in wanted) or (covered & wanted):
            if a.action_key not in keys:
                keys.append(a.action_key)
    return keys[:8]


# ---------------------------------------------------------------- saved jobs

def _latest_analysis(db: Session, user_id: int, job_id: int) -> SkillGapAnalysis | None:
    return (db.query(SkillGapAnalysis)
            .options(joinedload(SkillGapAnalysis.results).joinedload(SkillGapResult.job_requirement))
            .filter(SkillGapAnalysis.user_id == user_id, SkillGapAnalysis.job_description_id == job_id,
                    SkillGapAnalysis.status == AnalysisStatus.completed)
            .order_by(SkillGapAnalysis.created_at.desc(), SkillGapAnalysis.id.desc()).first())


def saved_job_match(db: Session, user_id: int, job: JobDescription) -> dict:
    a = _latest_analysis(db, user_id, job.id)
    base = dict(source="SAVED_JOB", job_description_id=job.id, title=job.title, target_role=job.target_role)
    if a is None:
        return dict(base, needs_analysis=True,
                    summary="Run a Skill Gap Analysis for this job to compare it with your profile.")
    reqs = [dict(name=r.job_requirement.skill_name, category=_v(r.job_requirement.category),
                 importance=_v(r.job_requirement.importance), classification=_v(r.classification))
            for r in a.results if r.job_requirement is not None]
    pct, bd = om.score(reqs, {r["name"].lower(): r["classification"] for r in reqs}, equal_weights=False)
    bd["recommended_action_keys"] = _action_keys(db, user_id, bd["missing"] + bd["partial"] + bd["transferable"], job.id)
    return dict(base, analysis_id=a.id, coverage_pct=pct, importance_detected=True, extracted_requirements=reqs,
                breakdown=bd, created_at=a.created_at, summary=om.summary(pct, "SAVED_JOB"),
                note="Requirements were extracted when you saved this job (Module 3); matching is Module 4's analysis.")


def saved_job_matches(db: Session, user_id: int) -> list[dict]:
    jobs = db.query(JobDescription).filter(JobDescription.user_id == user_id).order_by(JobDescription.id).all()
    out = [saved_job_match(db, user_id, j) for j in jobs]
    return sorted(out, key=lambda m: (m.get("coverage_pct") is None, -(m.get("coverage_pct") or 0), m["job_description_id"]))


# ---------------------------------------------------------------- pasted description

def _vocabulary(db: Session, user_id: int, user_skills: list[UserSkill]):
    saved = (db.query(JobRequirement.skill_name, JobRequirement.category)
             .join(JobDescription, JobDescription.id == JobRequirement.job_description_id)
             .filter(JobDescription.user_id == user_id).all())
    return om.build_vocabulary([(s.skill_name, _v(s.category)) for s in user_skills],
                               [(n, _v(c)) for n, c in saved], ALIASES)


def match_pasted(db: Session, user_id: int, req: OpportunityMatchRequest) -> OpportunityMatch:
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    reqs, detected = om.extract_requirements(req.job_description, _vocabulary(db, user_id, user_skills))
    if not reqs:
        raise HTTPException(422, "No recognisable skills were found in this job description.")
    for r in reqs:
        r["classification"] = _classify(r["name"], r["category"], user_skills)
    pct, bd = om.score(reqs, {r["name"].lower(): r["classification"] for r in reqs}, equal_weights=not detected)
    bd["recommended_action_keys"] = _action_keys(db, user_id, bd["missing"] + bd["partial"] + bd["transferable"])

    h = om.text_hash(req.job_description)
    row = db.query(OpportunityMatch).filter(OpportunityMatch.user_id == user_id,
                                            OpportunityMatch.source == OpportunitySource.USER_PROVIDED,
                                            OpportunityMatch.text_hash == h).first()
    if row is None:
        if db.query(OpportunityMatch).filter(OpportunityMatch.user_id == user_id).count() >= MAX_HISTORY:
            raise HTTPException(409, f"You have {MAX_HISTORY} saved comparisons. Delete some to add more.")
        row = OpportunityMatch(user_id=user_id, source=OpportunitySource.USER_PROVIDED, text_hash=h)
        db.add(row)
    row.title, row.company, row.source_url = req.title, req.company, req.source_url
    row.extracted_requirements = [dict(r, importance=r["importance"] if detected else "unspecified") for r in reqs]
    row.coverage_pct, row.breakdown = pct, bd
    row.created_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def match_out(row: OpportunityMatch) -> dict:
    detected = not any(r.get("importance") == "unspecified" for r in row.extracted_requirements or [])
    return dict(id=row.id, source=_v(row.source), job_description_id=row.job_description_id,
                source_url=row.source_url, title=row.title, company=row.company,
                coverage_pct=row.coverage_pct, importance_detected=detected,
                extracted_requirements=row.extracted_requirements, breakdown=row.breakdown,
                created_at=row.created_at, summary=om.summary(row.coverage_pct, "USER_PROVIDED"),
                note=("Skills were found by matching known skill names in the text; the description itself is not stored."
                      + ("" if detected else " No required/preferred sections were found, so all skills are weighted equally.")))


def match(db: Session, user_id: int, req: OpportunityMatchRequest) -> dict:
    if req.job_id is not None:
        job = db.query(JobDescription).filter(JobDescription.id == req.job_id,
                                              JobDescription.user_id == user_id).first()
        if job is None:
            raise HTTPException(404, "Job not found")
        return saved_job_match(db, user_id, job)
    return match_out(match_pasted(db, user_id, req))


def history(db: Session, user_id: int) -> list[dict]:
    rows = (db.query(OpportunityMatch).filter(OpportunityMatch.user_id == user_id)
            .order_by(OpportunityMatch.created_at.desc(), OpportunityMatch.id.desc()).all())
    return [match_out(r) for r in rows]


def delete(db: Session, user_id: int, match_id: int) -> None:
    row = db.query(OpportunityMatch).filter(OpportunityMatch.id == match_id,
                                            OpportunityMatch.user_id == user_id).first()
    if row is None:
        raise HTTPException(404, "Comparison not found")
    db.delete(row)
    db.commit()


def source_status() -> dict:
    return dict(saved_jobs_enabled=True, user_provided_enabled=True, job_api_configured=JOB_API_CONFIGURED,
                message=None if JOB_API_CONFIGURED else NO_SOURCE_MESSAGE)
