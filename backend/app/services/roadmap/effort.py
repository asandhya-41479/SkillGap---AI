"""Approximate learning-effort estimates. These are rough planning numbers, not predictions."""
import math

from app.core.roadmap_config import (
    CLASSIFICATION_EFFORT_MODIFIER,
    DEFAULT_EFFORT,
    HOURS_BY_SIZE,
    LEVEL_EFFORT_MODIFIER,
    MIN_ITEM_HOURS,
    REDUCED_SCOPE_FACTOR,
    SKILL_EFFORT,
)
from app.models.roadmap import EffortSize
from app.models.skill import SkillLevel
from app.models.skill_gap import MatchClassification


def _half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def base_size(key: str) -> EffortSize:
    return SKILL_EFFORT.get(key, DEFAULT_EFFORT)


def estimate_hours(
    size: EffortSize,
    classification: MatchClassification | None,
    level: SkillLevel,
) -> float:
    """size -> base hours, scaled by how much the user already has and their experience level."""
    hours = HOURS_BY_SIZE[size]
    hours *= CLASSIFICATION_EFFORT_MODIFIER.get(classification, 1.0) if classification else 1.0
    hours *= LEVEL_EFFORT_MODIFIER[level]
    return float(max(MIN_ITEM_HOURS, _half_up(hours)))


def reduced_hours(hours: float) -> float:
    return float(max(MIN_ITEM_HOURS, _half_up(hours * REDUCED_SCOPE_FACTOR)))