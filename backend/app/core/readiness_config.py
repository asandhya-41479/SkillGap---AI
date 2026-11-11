"""Module 6 settings in one place so every number is easy to find and change."""
from app.models.readiness import EvidenceKind as K, VerificationStatus as V

# How much a piece of evidence counts toward "demonstrated" (0-1). A skill's strength is the best of its rows.
EVIDENCE_STRENGTH = {
    (K.project_url, V.linked): 0.40,       # a link only; its content is never opened, so it must stay below a real repo
    (K.github_repo, V.verified): 1.00,     # repo is the user's own AND has a structural signal for the skill
    (K.github_repo, V.linked): 0.60,       # user's own repo, but no automatic check exists for this skill
    (K.github_repo, V.unverified): 0.25,   # checked: no signal found (or a fork). Same as plain learning evidence
    (K.github_repo, V.unavailable): 0.60,  # GitHub could not be reached; an outage must not punish the user
}
LEARNING_STRENGTH = 0.25   # a completed roadmap item without any attached evidence

# Module 2 auto-detected GitHub evidence (SkillEvidence.detected_via). Supporting evidence only, never proof.
MODULE2_EVIDENCE_STRENGTH = {
    "language": 0.60,   # GitHub reports code in this language in one of the user's repos
    "topic": 0.25,      # only a repo topic tag (self-applied label), so weak
}

MAX_EVIDENCE_PER_SKILL = 5
MAX_EVIDENCE_PER_USER = 100

# ---------- Career Readiness formula ----------
FORMULA_VERSION = "1.1"   # 1.1: project link 0.60 -> 0.40, Module 2 GitHub evidence counted
# score = 100 * sum(weight * component) / sum(weights of the components that exist). Components are in [0, 1].
COMPONENT_WEIGHTS = {"alignment": 0.30, "required_coverage": 0.25, "evidence": 0.20, "gap_health": 0.15, "roadmap": 0.10}
MIN_REQUIREMENTS = 3          # fewer analysed requirements than this -> "Not enough data"
NOT_ENOUGH_DATA = "Not enough data"
LABELS = [(30, "Getting started"), (50, "Building foundations"), (70, "Making progress"),
          (85, "Strong progress"), (101, "Highly aligned")]   # upper bound (exclusive) -> label

# ---------- Optional Gemini feedback (advisory wording only) ----------
FEEDBACK_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]  # same chain as Module 5
FEEDBACK_TIMEOUT_SECONDS = 8      # total time budget; after this the deterministic text is used
FEEDBACK_MIN_CHARS = 20
FEEDBACK_MAX_CHARS = 400
# Gemini text containing any of these is rejected (no hiring promises, probabilities or links).
FEEDBACK_BANNED_PATTERNS = [
    r"\bhir(e|ed|ing)\b", r"\bguarantee", r"\bjob offer", r"\bprobabilit", r"\bchance(s)?\b",
    r"\d+\s*%", r"\bdefinitely\b", r"\bjob[- ]ready\b", r"https?://", r"www\.",
]
