from app.models.job import Importance
from app.models.skill_gap import MatchClassification, PriorityLevel

# --- Similarity thresholds (Step 3/4 will validate these against real model output) ---
STRONG_MATCH_THRESHOLD = 0.80
PARTIAL_MATCH_THRESHOLD = 0.55
# below PARTIAL_MATCH_THRESHOLD => GAP

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