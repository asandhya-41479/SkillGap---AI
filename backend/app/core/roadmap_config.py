"""Static rules for the Module 5 roadmap rule engine.

Everything here is deterministic and reviewable. Skill keys are the lowercase form of the
canonical names produced by app.services.skill_normalization (e.g. "rest api", "llm"),
plus the small EXTRA_ALIASES table below.
"""
from app.models.job import Importance
from app.models.roadmap import EffortSize
from app.models.skill import SkillLevel
from app.models.skill_gap import MatchClassification, PriorityLevel

# ---------- Effort (approximate hours; always shown as "≈") ----------
HOURS_BY_SIZE: dict[EffortSize, float] = {
    EffortSize.small: 6,
    EffortSize.medium: 14,
    EffortSize.large: 28,
}
# A partial match means the user already has part of it; a transferable match means related
# foundations exist. A full gap costs the full base effort.
CLASSIFICATION_EFFORT_MODIFIER: dict[MatchClassification, float] = {
    MatchClassification.gap: 1.0,
    MatchClassification.transferable: 0.75,
    MatchClassification.partial: 0.5,
}
LEVEL_EFFORT_MODIFIER: dict[SkillLevel, float] = {
    SkillLevel.beginner: 1.25,
    SkillLevel.intermediate: 1.0,
    SkillLevel.advanced: 0.8,
}
MIN_ITEM_HOURS = 2
REDUCED_SCOPE_FACTOR = 0.6   # HIGH items that do not fit are retried at this fraction ("core topics only")


# ---------- Time budget ----------
CAPACITY_TOLERANCE = 0.10        # plans may use up to 110% of hours_per_week * duration_weeks
TIGHT_PLAN_UTILISATION = 0.90    # above this, warn that there is little buffer

# ---------- Ordering ranks (lower sorts first) ----------
PRIORITY_RANK: dict[PriorityLevel, int] = {
    PriorityLevel.high: 0,
    PriorityLevel.medium: 1,
    PriorityLevel.low: 2,
    PriorityLevel.none: 3,
}
IMPORTANCE_RANK: dict[Importance, int] = {
    Importance.required: 0,
    Importance.preferred: 1,
    Importance.optional: 2,
}
CLASSIFICATION_RANK: dict[MatchClassification, int] = {
    MatchClassification.gap: 0,
    MatchClassification.transferable: 1,
    MatchClassification.partial: 2,
    MatchClassification.strong: 3,
}

# ---------- Skill keys ----------
# Extra aliases applied to the lowercase, Module-2-normalized name.
EXTRA_ALIASES: dict[str, str] = {
    "embedding": "embeddings",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "cicd": "ci/cd",
    "ci cd": "ci/cd",
    "vector database": "vector databases",

    "vector db": "vector databases",
    "natural language processing": "nlp",
    "torch": "pytorch",
}

DISPLAY_NAMES: dict[str, str] = {
    "python": "Python", "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "rest api": "REST API", "sql": "SQL", "postgresql": "PostgreSQL", "sqlalchemy": "SQLAlchemy",
    "docker": "Docker", "kubernetes": "Kubernetes", "linux": "Linux", "git": "Git",
    "ci/cd": "CI/CD", "deployment": "Deployment", "aws": "AWS",
    "machine learning": "Machine Learning", "deep learning": "Deep Learning",
    "scikit-learn": "scikit-learn", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
    "pandas": "pandas", "numpy": "NumPy", "nlp": "NLP", "embeddings": "Embeddings",
    "vector databases": "Vector Databases", "rag": "RAG", "llm": "LLM", "langchain": "LangChain",
    "mlops": "MLOps", "javascript": "JavaScript", "typescript": "TypeScript", "react": "React",
    "node.js": "Node.js", "next.js": "Next.js", "vue": "Vue",
}

# ---------- Base effort per skill (unknown skills default to medium) ----------
_SMALL = ["git", "numpy", "html", "css"]
_MEDIUM = [
    "fastapi", "flask", "django", "docker", "postgresql", "sql", "embeddings", "langchain",
    "rest api", "react", "node.js", "typescript", "javascript", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "sqlalchemy", "ci/cd", "deployment", "vector databases",
    "next.js", "vue", "llm", "linux",
]
_LARGE = [
    "python", "machine learning", "deep learning", "kubernetes", "aws", "rag", "mlops", "nlp",
    "google cloud platform", "java", "c++",
]
SKILL_EFFORT: dict[str, EffortSize] = {
    **{k: EffortSize.small for k in _SMALL},

    **{k: EffortSize.medium for k in _MEDIUM},
    **{k: EffortSize.large for k in _LARGE},
}
DEFAULT_EFFORT = EffortSize.medium

# ---------- Prerequisites ----------
# hard: must be learned first. If missing from the profile, it is scheduled as a
#       supplementary item; if it cannot be scheduled, its dependents are deferred.
# soft: ordering preference only, applied when both skills are in the roadmap.
DEPENDENCIES: dict[str, dict[str, list[str]]] = {
    "fastapi": {"hard": ["python"], "soft": ["rest api"]},
    "flask": {"hard": ["python"], "soft": ["rest api"]},
    "django": {"hard": ["python"]},
    "rest api": {"soft": ["python"]},
    "docker": {"soft": ["linux"]},
    "kubernetes": {"hard": ["docker"]},
    "deployment": {"hard": ["docker"], "soft": ["rest api"]},
    "ci/cd": {"hard": ["git"], "soft": ["docker"]},
    "aws": {"soft": ["linux"]},
    "postgresql": {"hard": ["sql"]},
    "sqlalchemy": {"hard": ["python", "sql"]},
    "pandas": {"hard": ["python"]},
    "numpy": {"hard": ["python"]},
    "machine learning": {"hard": ["python"]},
    "scikit-learn": {"hard": ["python"], "soft": ["machine learning"]},
    "deep learning": {"hard": ["machine learning"]},
    "pytorch": {"hard": ["python", "machine learning"]},
    "tensorflow": {"hard": ["python", "machine learning"]},
    "nlp": {"hard": ["machine learning"]},
    "embeddings": {"hard": ["python", "machine learning"]},
    "vector databases": {"hard": ["embeddings"]},
    "rag": {"hard": ["embeddings", "python"], "soft": ["llm", "vector databases"]},

    "llm": {"soft": ["python"]},
    "langchain": {"hard": ["python"], "soft": ["llm"]},
    "mlops": {"hard": ["docker", "machine learning"]},
    "react": {"hard": ["javascript"]},
    "next.js": {"hard": ["react"]},
    "node.js": {"hard": ["javascript"]},
    "typescript": {"hard": ["javascript"]},
    "vue": {"hard": ["javascript"]},
}

# ---------- User-facing messages ----------
NOTE_TIME_INSUFFICIENT = (
    "The available time may not be sufficient to cover all identified gaps. "
    "These high-priority skills should be completed first."
)
NOTE_TIGHT_PLAN = (
    "This plan uses about {pct}% of your available time, leaving little buffer. "
    "Treat the hour estimates as approximate."
)
NOTE_NO_GAPS = (
    "No skill gaps to address for this analysis: every requirement is already strongly matched "
    "by your profile."
)