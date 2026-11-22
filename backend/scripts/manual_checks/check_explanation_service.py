from types import SimpleNamespace

from app.models.job import Importance
from app.models.skill_gap import MatchClassification, MatchMethod
from app.services.explanation_service import _deterministic_explanation, generate_explanation
from app.services.skill_gap_engine import GapEngineResult
from app.services.skill_matching_service import MatchCandidate


def fake_result(classification, matched_skill_name, requirement_name="FastAPI", importance=Importance.required):
    requirement = SimpleNamespace(skill_name=requirement_name, importance=importance)
    matched = SimpleNamespace(skill_name=matched_skill_name) if matched_skill_name else None
    match = MatchCandidate(
        matched_user_skill=matched,
        similarity_score=0.75 if matched else None,
        classification=classification,
        match_method=MatchMethod.semantic,
    )
    return GapEngineResult(job_requirement=requirement, match=match, priority=None)


cases = [
    fake_result(MatchClassification.strong, "FastAPI"),
    fake_result(MatchClassification.transferable, "Python"),
    fake_result(MatchClassification.gap, None, requirement_name="Docker"),
]

if __name__ == "__main__":
    print("--- Deterministic only ---")
    for c in cases:
        print(_deterministic_explanation(c))


    print("\n--- Via generate_explanation (Gemini if available, else fallback) ---")
    for c in cases:
        text, source = generate_explanation(c)
        print(f"[{source.value}] {text}")