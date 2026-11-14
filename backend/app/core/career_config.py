"""Module 7 settings in one place (same pattern as readiness_config / skill_gap_config).
Every threshold and weight of the Career Action Engine lives here so it is easy to find, explain and change.
"""

ENGINE_VERSION = "1.0"   # part of the plan cache key: changing rules invalidates cached plans

# ---------- Skill state ----------
# A skill counts as "proven" when its best evidence strength (Module 6 evidence_strengths) reaches this value.
# Same 0.60 line Module 6 uses for "solid evidence" (verified repo 1.0, own repo 0.6, Module 2 language 0.6;
# a plain project link 0.40 and learning-only 0.25 stay below it).
PROVEN_THRESHOLD = 0.60

# ---------- Priority formula ----------
# score = 100 * (0.35 R + 0.25 S + 0.20 I + 0.10 D + 0.10 (1 - P))
PRIORITY_WEIGHTS = {"requirement": 0.35, "severity": 0.25, "importance": 0.20, "dependency": 0.10, "progress": 0.10}

# R: Module 4 importance, same ratios as IMPORTANCE_WEIGHT (2 : 1 : 0.5), scaled to 0-1
REQUIREMENT_FACTOR = {"required": 1.0, "preferred": 0.5, "optional": 0.25}

# S: how far the skill is from "proven"
SEVERITY_FACTOR = {
    "NO_KNOWLEDGE": 1.0,        # Module 4 gap
    "TRANSFERABLE": 0.85,       # Module 4 transferable: a related foundation exists, the skill itself does not
    "PARTIAL": 0.6,             # Module 4 partial
    "KNOWN_NO_EVIDENCE": 0.4,   # strong match (or roadmap finished) but evidence < PROVEN_THRESHOLD
    "PROVEN": 0.1,
}

# I: Module 4 priority (already combines importance x classification via PRIORITY_TABLE)
IMPORTANCE_FACTOR = {"high": 1.0, "medium": 0.6, "low": 0.3, "none": 0.1}
# Module 4 priority measures the KNOWLEDGE gap only, so a strong match is "none" there even when it has no
# proof. For evidence-only states (KNOWN_NO_EVIDENCE) I comes from importance instead: required evidence
# matters like a medium gap. Without this, "learn a preferred skill" outranked "prove a required skill".
EVIDENCE_IMPORTANCE_FACTOR = {"required": 0.6, "preferred": 0.3, "optional": 0.1}

# P: Module 5 roadmap item progress
PROGRESS_FACTOR = {None: 0.0, "not_started": 0.0, "skipped": 0.0, "in_progress": 0.4, "completed": 0.8}
PROGRESS_COMPLETED_WITH_PRACTICAL = 1.0

HIGH_THRESHOLD = 65.0
MEDIUM_THRESHOLD = 40.0

TOP_ACTIONS = 5          # shown on the dashboard
MAX_ACTIONS = 12         # total active actions per plan (keeps the plan focused)

# ---------- Career status (approved rules, evaluated top-down) ----------
# R = % required skills strong, C = critical gaps (required gap/transferable), E = % required skills proven,
# P = roadmap %, Q = % HIGH interview topics prepared, S = Module 6 readiness score.
STATUS_RULES = [
    ("READY_TO_APPLY", {"R": (">=", 85), "C": ("<=", 0), "E": (">=", 70), "P": (">=", 70),
                        "Q": (">=", 60), "S": (">=", 75)}),
    ("NEAR_READY", {"R": (">=", 70), "C": ("<=", 1), "E": (">=", 50), "S": (">=", 60)}),
]
DEVELOPING_RULE = {"R": (">=", 40), "S": (">=", 40)}    # ANY one of these (approved "or")
STATUS_LABELS = {
    "R": "Required skills covered (%)",
    "C": "Critical gaps (required skills missing)",
    "E": "Required skills with solid evidence (%)",
    "P": "Roadmap progress (%)",
    "Q": "High-priority interview topics prepared (%)",
    "S": "Career Readiness score",
}

# APPLY checklist: only generated at NEAR_READY / READY_TO_APPLY. Never names companies or openings.
APPLY_SCORE = {"READY_TO_APPLY": 70.0, "NEAR_READY": 45.0}
# NEAR_READY gets only the first items (finish the work first); READY_TO_APPLY gets the full checklist
APPLY_ITEMS = {"READY_TO_APPLY": 4, "NEAR_READY": 2}

# ---------- Step 4: Gemini explanation layer (wording only, never facts) ----------
EXPLAIN_ENABLED = True
EXPLAIN_MAX_ACTIONS = 8          # only the top actions are explained (cost + latency); the rest keep their reason
EXPLAIN_TIMEOUT_SECONDS = 15     # total budget for the call; after it the deterministic reason is used
EXPLAIN_MIN_CHARS = 20
EXPLAIN_MAX_CHARS = 300          # per field (why / how_it_connects)
# Rejected in Gemini text. First part = Module 6 FEEDBACK_BANNED_PATTERNS (a test keeps them in sync),
# then Module 7 extras (salaries, companies, openings, mastery claims, timelines).
EXPLAIN_BANNED_PATTERNS = [
    r"\bhir(e|ed|ing)\b", r"\bguarantee", r"\bjob offer", r"\bprobabilit", r"\bchance(s)?\b",
    r"\d+\s*%", r"\bdefinitely\b", r"\bjob[- ]ready\b", r"https?://", r"www\.",
    r"\bsalar(y|ies)\b", r"\blpa\b", r"\blakh", r"₹", r"\$\s*\d", r"\brecruiter", r"\boffer\b",
    r"\bmaster(ed|y)\b", r"\bexpert\b", r"\bcompan(y|ies)\b", r"\bopening(s)?\b", r"\bweeks?\b", r"\bmonths?\b",
]

# ---------- Step 6: interview preparation ----------
PREP_MAX_GAP_SKILLS = 6        # gap topics: only the most important skills (focused, not 500 questions)
PREP_SUBTOPICS_PER_SKILL = 5
PREP_MAX_PROJECT_FACTS = 6     # project questions about the user's own SkillGap AI build
PREP_QUESTIONS_MIN = 2         # fewer valid Gemini questions than this -> deterministic questions
PREP_QUESTIONS_MAX = 5
PREP_QUESTION_MIN_CHARS = 15
PREP_QUESTION_MAX_CHARS = 200
PREP_TIMEOUT_SECONDS = 15
