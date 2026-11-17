from dataclasses import dataclass

from app.core.skill_gap_config import (
    CLASSIFICATION_CREDIT,
    IMPORTANCE_WEIGHT,
    PRIORITY_TABLE,
)
from app.models.job import JobDescription, JobRequirement
from app.models.skill import UserSkill
from app.models.skill_gap import MatchClassification, PriorityLevel
from app.services.skill_matching_service import MatchCandidate, find_best_match


@dataclass
class GapEngineResult:
    """One requirement's full analysis — everything Step 7 will persist as a SkillGapResult row."""
    job_requirement: JobRequirement
    match: MatchCandidate
    priority: PriorityLevel


_STRENGTH = {
    MatchClassification.strong: 3,
    MatchClassification.partial: 2,
    MatchClassification.transferable: 1,
    MatchClassification.gap: 0,
}


def _match_requirement(requirement: JobRequirement, user_skills: list[UserSkill]) -> MatchCandidate:
    """Best match for the requirement OR any of its alternatives.

    "Vector Databases" with alternatives [Pinecone, FAISS, Chroma] is satisfied by any one of
    them, so each name is matched and the strongest result wins (ties: higher similarity).
    A requirement without alternatives is matched exactly as before.
    """
    category = requirement.category.value
    names = [requirement.skill_name] + list(getattr(requirement, "alternatives", None) or [])
    best: MatchCandidate | None = None
    for name in names:
        candidate = find_best_match(requirement_skill_name=name, requirement_category=category,
                                    user_skills=user_skills)
        if best is None or (_STRENGTH[candidate.classification], candidate.similarity_score or 0.0) > (
                _STRENGTH[best.classification], best.similarity_score or 0.0):
            best = candidate
    return best


def _priority_for(requirement: JobRequirement, classification: MatchClassification) -> PriorityLevel:
    return PRIORITY_TABLE.get((requirement.importance, classification), PriorityLevel.none)


def run_gap_analysis(
    job: JobDescription,
    user_skills: list[UserSkill],
) -> tuple[list[GapEngineResult], float | None]:
    """
    Returns (per-requirement results, overall alignment score).


    Alignment score formula (Step 1 §13):
        sum(weight(requirement) * credit(classification)) / sum(weight(requirement)) * 100
    weight comes from requirement importance (required > preferred > optional);
    credit comes from match classification (strong > partial > transferable > gap).

    Returns (results, None) if the job has no requirements at all — an alignment
    score is undefined with a zero-length denominator, and Step 7's API layer
    is responsible for surfacing that as a clear "no requirements to compare"
    state rather than this function inventing a placeholder score.
    """
    requirements = job.requirements

    if not requirements:
        return [], None

    results: list[GapEngineResult] = []
    weighted_credit_sum = 0.0
    weight_sum = 0.0

    for requirement in requirements:
        match = _match_requirement(requirement, user_skills)
        priority = _priority_for(requirement, match.classification)

        results.append(GapEngineResult(job_requirement=requirement, match=match, priority=priority))

        weight = IMPORTANCE_WEIGHT[requirement.importance]
        credit = CLASSIFICATION_CREDIT[match.classification]
        weighted_credit_sum += weight * credit

        weight_sum += weight

    overall_alignment_score = round((weighted_credit_sum / weight_sum) * 100, 2) if weight_sum else None

    return results, overall_alignment_score