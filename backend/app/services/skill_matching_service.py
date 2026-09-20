from dataclasses import dataclass

from app.core.skill_gap_config import (
    CATEGORY_FLOOR,
    ECOSYSTEM_TRANSFERABLE_PAIRS,
    KNOWN_FALSE_FRIENDS,
    PARTIAL_MATCH_THRESHOLD,
    STRONG_MATCH_THRESHOLD,
)
from app.models.skill import UserSkill
from app.models.skill_gap import MatchClassification, MatchMethod
from app.services.embedding_service import EmbeddingServiceUnavailable, embedding_service
from app.services.skill_normalization import normalize_skill_name


@dataclass
class MatchCandidate:
    """One job requirement's best match against the user's skill set."""
    matched_user_skill: UserSkill | None
    similarity_score: float | None
    classification: MatchClassification
    match_method: MatchMethod


def _is_false_friend(name_a: str, name_b: str) -> bool:
    pair = frozenset({name_a.strip().lower(), name_b.strip().lower()})
    return pair in KNOWN_FALSE_FRIENDS


def _is_ecosystem_pair(name_a: str, name_b: str) -> bool:
    pair = frozenset({name_a.strip().lower(), name_b.strip().lower()})
    return pair in ECOSYSTEM_TRANSFERABLE_PAIRS


def _embed_text(skill_name: str, category: str) -> str:
    """Matches the exact representation validated in Step 3 testing."""
    return f"{skill_name} ({category})"


def classify_similarity(
    similarity: float,
    same_category: bool,
    is_ecosystem_pair: bool = False,
) -> MatchClassification:
    """
    Pure classification logic — no I/O, easy to unit test in isolation.

    Category-floor rule: a same-category match below STRONG but above the
    floor is never dropped to Gap purely on raw score (Step 3 finding:
    Flask/FastAPI scored too low on raw similarity alone despite being
    genuinely related — same category is a stronger signal than the number).

    Ecosystem-pair rule: cross-category "foundation" relationships (e.g.
    Python -> FastAPI) score too low on raw similarity to distinguish from
    noise (Step 4 finding: Python/FastAPI ~= Python/Photoshop). A curated
    lookup catches these explicitly rather than trusting the raw number.
    """
    if similarity >= STRONG_MATCH_THRESHOLD:
        return MatchClassification.strong
    if similarity >= PARTIAL_MATCH_THRESHOLD:
        return MatchClassification.partial if same_category else MatchClassification.transferable
    if same_category and similarity >= CATEGORY_FLOOR:
        return MatchClassification.partial
    if is_ecosystem_pair:
        return MatchClassification.transferable
    return MatchClassification.gap


def find_best_match(
    requirement_skill_name: str,
    requirement_category: str,
    user_skills: list[UserSkill],
) -> MatchCandidate:
    """
    Layer 1: normalization (already applied to stored names, re-applied here
             defensively in case requirement_skill_name arrives un-normalized)
    Layer 2: exact canonical match
    Layer 3: classify EVERY candidate individually via embedding similarity,
             then pick the best result by classification strength (not by
             raw score alone — see _RANK below)
    Layer 4: (folded into Layer 3's per-candidate classification)
    """
    if not user_skills:
        return MatchCandidate(
            matched_user_skill=None,
            similarity_score=None,
            classification=MatchClassification.gap,
            match_method=MatchMethod.none,
        )

    normalized_requirement = normalize_skill_name(requirement_skill_name)

    # Layer 2 — exact canonical match short-circuits everything else
    for skill in user_skills:
        if normalize_skill_name(skill.skill_name) == normalized_requirement:
            return MatchCandidate(
                matched_user_skill=skill,
                similarity_score=1.0,
                classification=MatchClassification.strong,
                match_method=MatchMethod.exact,
            )

    # Layer 3 — classify EVERY candidate individually, then pick the best
    # overall result by classification strength, not by raw score alone.
    # Raw score is only used to break ties within the same classification —
    # at low similarity levels, a hairline score difference is noise and
    # must not be allowed to silently skip a known ecosystem relationship.
    _RANK = {
        MatchClassification.strong: 3,
        MatchClassification.partial: 2,
        MatchClassification.transferable: 1,
        MatchClassification.gap: 0,
    }

    try:
        requirement_text = _embed_text(normalized_requirement, requirement_category)
        best_candidate: tuple[UserSkill, float, MatchClassification] | None = None

        for skill in user_skills:
            if _is_false_friend(skill.skill_name, requirement_skill_name):
                continue  # lexically similar but known to be unrelated — excluded

            skill_text = _embed_text(skill.skill_name, skill.category.value)
            score = embedding_service.cosine_similarity(requirement_text, skill_text)
            same_category = skill.category.value == requirement_category
            classification = classify_similarity(
                score,
                same_category,
                is_ecosystem_pair=_is_ecosystem_pair(skill.skill_name, requirement_skill_name),
            )

            if best_candidate is None:
                best_candidate = (skill, score, classification)
                continue

            _, best_score_so_far, best_classification_so_far = best_candidate
            if _RANK[classification] > _RANK[best_classification_so_far]:
                best_candidate = (skill, score, classification)
            elif _RANK[classification] == _RANK[best_classification_so_far] and score > best_score_so_far:
                best_candidate = (skill, score, classification)

        if best_candidate is None:
            # every candidate was excluded as a false friend
            return MatchCandidate(
                matched_user_skill=None,
                similarity_score=None,
                classification=MatchClassification.gap,
                match_method=MatchMethod.none,
            )

        best_skill, best_score, classification = best_candidate

        return MatchCandidate(
            matched_user_skill=best_skill if classification != MatchClassification.gap else None,
            similarity_score=round(best_score, 4),
            classification=classification,
            match_method=MatchMethod.semantic,
        )

    except EmbeddingServiceUnavailable:
        # Step 1 §20 edge case — fail safe, don't crash the whole analysis
        return MatchCandidate(
            matched_user_skill=None,
            similarity_score=None,
            classification=MatchClassification.gap,
            match_method=MatchMethod.none,
        )