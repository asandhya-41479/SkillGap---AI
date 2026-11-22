from types import SimpleNamespace

from app.models.skill_gap import MatchClassification, MatchMethod
from app.services.skill_matching_service import find_best_match


def fake_skill(name: str, category: str):
    # Mimics the two attributes find_best_match actually reads from UserSkill
    return SimpleNamespace(skill_name=name, category=SimpleNamespace(value=category))


cases = [
    ("Python", "programming_language", [fake_skill("Python", "programming_language")]),
    ("React.js", "framework", [fake_skill("React", "framework")]),
    ("SQL databases", "database", [fake_skill("PostgreSQL", "database")]),
    ("FastAPI", "framework", [fake_skill("Python", "programming_language")]),
    ("FastAPI", "framework", [fake_skill("Flask", "framework")]),
    ("JavaScript", "programming_language", [fake_skill("Java", "programming_language")]),
    ("Docker", "devops", []),
]

if __name__ == "__main__":
    for requirement, category, skills in cases:
        result = find_best_match(requirement, category, skills)
        print(
            f"{requirement!r:20} ({category:22}) -> "
            f"{result.classification.value:12} "
            f"method={result.match_method.value:9} "
            f"score={result.similarity_score}"
        )