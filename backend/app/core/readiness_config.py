"""Module 6 settings in one place so every number is easy to find and change.
Step 5 adds the readiness formula weights to this file."""
from app.models.readiness import EvidenceKind as K, VerificationStatus as V

# How much a piece of evidence counts toward "demonstrated" (0-1). A skill's strength is the best of its rows.
EVIDENCE_STRENGTH = {
    (K.project_url, V.linked): 0.60,       # a link only; its content is never opened
    (K.github_repo, V.verified): 1.00,     # repo is the user's own AND has a structural signal for the skill
    (K.github_repo, V.linked): 0.60,       # user's own repo, but no automatic check exists for this skill
    (K.github_repo, V.unverified): 0.25,   # checked: no signal found (or a fork). Same as plain learning evidence
    (K.github_repo, V.unavailable): 0.60,  # GitHub could not be reached; an outage must not punish the user
}
LEARNING_STRENGTH = 0.25   # a completed roadmap item without any attached evidence

MAX_EVIDENCE_PER_SKILL = 5
MAX_EVIDENCE_PER_USER = 100

# ---------- Career Readiness formula (Step 5) ----------
FORMULA_VERSION = "1.0"
# score = 100 * sum(weight * component) / sum(weights of the components that exist). Components are in [0, 1].
COMPONENT_WEIGHTS = {"alignment": 0.30, "required_coverage": 0.25, "evidence": 0.20, "gap_health": 0.15, "roadmap": 0.10}
MIN_REQUIREMENTS = 3          # fewer analysed requirements than this -> "Not enough data"
NOT_ENOUGH_DATA = "Not enough data"
LABELS = [(30, "Getting started"), (50, "Building foundations"), (70, "Making progress"),
          (85, "Strong progress"), (101, "Highly aligned")]   # upper bound (exclusive) -> label