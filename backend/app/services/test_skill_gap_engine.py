from types import SimpleNamespace

from app.models.job import Importance
from app.services.skill_gap_engine import run_gap_analysis


def fake_requirement(skill_name: str, category: str, importance: Importance):
    return SimpleNamespace(skill_name=skill_name, category=SimpleNamespace(value=category), importance=importance)


def fake_skill(name: str, category: str):
    return SimpleNamespace(skill_name=name, category=SimpleNamespace(value=category))


fake_job = SimpleNamespace(requirements=[
    fake_requirement("Python", "programming_language", Importance.required),
    fake_requirement("Docker", "devops", Importance.required),
    fake_requirement("SQL databases", "database", Importance.preferred),
    fake_requirement("Kubernetes", "devops", Importance.optional),
])

fake_user_skills = [
    fake_skill("Python", "programming_language"),
    fake_skill("PostgreSQL", "database"),
]

if __name__ == "__main__":
    results, score = run_gap_analysis(fake_job, fake_user_skills)
    for r in results:
        print(
            f"{r.job_requirement.skill_name:20} "
            f"importance={r.job_requirement.importance.value:10} "

            f"-> {r.match.classification.value:12} "
            f"priority={r.priority.value}"
        )
    print(f"\nOverall Alignment Score: {score}")