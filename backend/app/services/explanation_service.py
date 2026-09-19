import logging

from google import genai

from app.core.config import settings
from app.models.skill_gap import ExplanationSource, MatchClassification
from app.services.skill_gap_engine import GapEngineResult

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.gemini_api_key)

_EXPLANATION_PROMPT = """You are writing a one-sentence explanation for a skill-gap analysis result.
You must NOT invent facts. Use only the information given below.

Job requirement: {requirement_name} (importance: {importance})
Classification: {classification}
Best matching user skill: {matched_skill}
Similarity score: {similarity_score}

Write exactly one plain sentence explaining this result to the user. Do not
mention similarity scores or embeddings. Do not suggest the user is more or
less proficient than what is stated. Output the sentence only, no preamble."""


def _deterministic_explanation(result: GapEngineResult) -> str:
    """
    Template fallback — always available, never depends on Gemini.
    This is also what Step 9's tests can assert against deterministically.
    """
    requirement_name = result.job_requirement.skill_name
    matched = result.match.matched_user_skill


    if result.match.classification == MatchClassification.strong:
        return f"Your {matched.skill_name} skill directly matches the {requirement_name} requirement."

    if result.match.classification == MatchClassification.partial:
        return (
            f"Your {matched.skill_name} skill is related to {requirement_name}, "
            f"but may not fully cover this requirement."
        )

    if result.match.classification == MatchClassification.transferable:
        return (
            f"Your {matched.skill_name} skill provides a relevant foundation, "
            f"but {requirement_name} is not directly demonstrated."
        )

    return f"No demonstrated skill was found in your profile for {requirement_name}."


def generate_explanation(result: GapEngineResult) -> tuple[str, ExplanationSource]:
    """
    Returns (explanation_text, source). Always succeeds — Gemini failure
    falls back to the deterministic template rather than propagating,
    per Step 1 §11: the architecture must work even if Gemini is unavailable.
    """
    matched_skill_name = result.match.matched_user_skill.skill_name if result.match.matched_user_skill else "none"

    prompt = _EXPLANATION_PROMPT.format(
        requirement_name=result.job_requirement.skill_name,
        importance=result.job_requirement.importance.value,
        classification=result.match.classification.value,
        matched_skill=matched_skill_name,

        similarity_score=result.match.similarity_score,
    )

    try:
        response = _client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        text = response.text.strip()
        if not text:
            raise ValueError("Gemini returned empty text")
        return text, ExplanationSource.gemini
    except Exception:
        logger.warning("Gemini explanation failed, using deterministic fallback", exc_info=True)
        return _deterministic_explanation(result), ExplanationSource.deterministic