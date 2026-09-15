from app.models.job import Importance, RequirementCategory
from app.services.skill_normalization import normalize_skill_name

VALID_CATEGORIES = {c.value for c in RequirementCategory}
VALID_IMPORTANCE = {i.value for i in Importance}


def process_extraction(raw_items: list[dict]) -> list[dict]:
    """Validate, normalize, and deduplicate Gemini's raw extraction output.
    Malformed individual entries are dropped rather than failing the whole batch."""
    seen: dict[str, dict] = {}

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        normalized_name = normalize_skill_name(name)

        category = item.get("category")
        if category not in VALID_CATEGORIES:
            category = RequirementCategory.other.value

        importance = item.get("importance")
        if importance not in VALID_IMPORTANCE:
            importance = Importance.optional.value

        # Deduplicate by normalized name; keep the more important of the two if seen twice
        existing = seen.get(normalized_name)

        if existing is None or _importance_rank(importance) > _importance_rank(existing["importance"]):
            seen[normalized_name] = {"skill_name": normalized_name, "category": category, "importance": importance}

    return list(seen.values())


def _importance_rank(importance: str) -> int:
    return {"required": 2, "preferred": 1, "optional": 0}.get(importance, 0)