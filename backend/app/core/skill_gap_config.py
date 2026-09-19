from app.models.job import Importance
from app.models.skill_gap import MatchClassification, PriorityLevel

# --- Similarity thresholds (validated against real model output, Step 3) ---
STRONG_MATCH_THRESHOLD = 0.80
PARTIAL_MATCH_THRESHOLD = 0.45
CATEGORY_FLOOR = 0.15  # below this, even a same-category match is treated as Gap

# Curated overrides for lexically-similar-but-semantically-different pairs
# (normalized, lowercase skill names, unordered pair)
KNOWN_FALSE_FRIENDS: set[frozenset[str]] = {
    frozenset({"java", "javascript"}),
}

# --- Alignment score weighting ---
IMPORTANCE_WEIGHT = {
    Importance.required: 2.0,
    Importance.preferred: 1.0,
    Importance.optional: 0.5,
}

CLASSIFICATION_CREDIT = {
    MatchClassification.strong: 1.0,
    MatchClassification.partial: 0.5,
    MatchClassification.transferable: 0.25,
    MatchClassification.gap: 0.0,
}

# --- Priority lookup table: (importance, classification) -> priority ---
PRIORITY_TABLE = {
    (Importance.required, MatchClassification.gap): PriorityLevel.high,
    (Importance.required, MatchClassification.transferable): PriorityLevel.high,
    (Importance.required, MatchClassification.partial): PriorityLevel.medium,
    (Importance.required, MatchClassification.strong): PriorityLevel.none,

    (Importance.preferred, MatchClassification.gap): PriorityLevel.medium,
    (Importance.preferred, MatchClassification.transferable): PriorityLevel.low,
    (Importance.preferred, MatchClassification.partial): PriorityLevel.low,
    (Importance.preferred, MatchClassification.strong): PriorityLevel.none,

    (Importance.optional, MatchClassification.gap): PriorityLevel.low,
    (Importance.optional, MatchClassification.transferable): PriorityLevel.low,
    (Importance.optional, MatchClassification.partial): PriorityLevel.low,
    (Importance.optional, MatchClassification.strong): PriorityLevel.none,
}

# Curated cross-category "foundation" relationships. Raw embedding similarity
# can't reliably distinguish these from unrelated pairs at this model's
# resolution (validated in Step 4: Python/FastAPI ~= Python/Photoshop in raw
# score), so known ecosystem relationships are captured explicitly instead.
# Format: {(language_or_base_skill, dependent_skill), ...} — order matters,
# read as "base skill provides a foundation for dependent skill".
ECOSYSTEM_TRANSFERABLE_PAIRS: set[frozenset[str]] = {
    frozenset({"python", "fastapi"}),
    frozenset({"python", "flask"}),
    frozenset({"python", "django"}),
    frozenset({"javascript", "react"}),
    frozenset({"javascript", "node.js"}),
    frozenset({"javascript", "express"}),
}