"""Module 7 Step 3: the deterministic Career Action Engine. Pure: no database, no network, no Gemini.

Pipeline:  SkillInput -> skill state -> action category -> priority score -> ranked actions (+ APPLY checklist)

1. State   (from Module 4 classification + Module 6 evidence strength + Module 5 roadmap status)
     gap -> NO_KNOWLEDGE, transferable -> TRANSFERABLE, partial -> PARTIAL,
     strong -> PROVEN if evidence >= PROVEN_THRESHOLD else KNOWN_NO_EVIDENCE.
     A gap/transferable/partial skill whose roadmap item is COMPLETED but still has no solid evidence is
     treated as KNOWN_NO_EVIDENCE: the learning is done, the proof is missing.
2. Category
     NO_KNOWLEDGE / TRANSFERABLE -> LEARN,  PARTIAL -> PRACTICE,
     KNOWN_NO_EVIDENCE -> PROVE if Module 6 can verify the skill from repo files, else BUILD
                          (problem_solving -> PRACTICE, conceptual -> PREPARE),
     PROVEN -> PREPARE.
3. Priority  score = 100 * (0.35 R + 0.25 S + 0.20 I + 0.10 D + 0.10 (1 - P))  -> HIGH / MEDIUM / LOW
     I uses Module 4 priority for knowledge gaps and importance for evidence-only gaps.
     Overrides: a required gap that other open skills depend on is always HIGH; optional skills are at most LOW.
4. Order   priority band -> prerequisite depth (foundations first) -> score -> in-progress momentum.
"""
from dataclasses import asdict, dataclass, field

from app.core import career_config as cfg
from app.schemas.career import CareerInputs, SkillInput
from app.services.career import catalog
from app.services.career.career_status import StatusResult, evaluate_status

_IMPORTANCE_RANK = {"required": 0, "preferred": 1, "optional": 2}
_BAND_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


@dataclass
class ActionCandidate:
    action_key: str
    category: str
    priority: str
    priority_score: float
    title: str
    reason: str
    reason_codes: list[str]
    evidence_required: list[str]
    skill_name: str | None = None
    importance: str | None = None
    state: str | None = None
    classification: str | None = None
    evidence_strength: float = 0.0
    job_requirement_id: int | None = None
    gap_result_id: int | None = None
    roadmap_item_id: int | None = None
    roadmap_status: str | None = None
    rank: int = 0
    depth: int = 0           # unlearned-prerequisite depth (ordering only)
    covers: list[str] = field(default_factory=list)   # skill keys a project action proves (Step 5)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EngineResult:
    status: StatusResult
    actions: list[ActionCandidate]
    skill_priorities: list[dict] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)        # Step 5
    evidence_gaps: list[dict] = field(default_factory=list)   # Step 5


# ---------------------------------------------------------------- 1. state

def skill_state(s: SkillInput) -> str:
    proven = s.evidence_strength >= cfg.PROVEN_THRESHOLD
    if s.classification == "strong":
        return "PROVEN" if proven else "KNOWN_NO_EVIDENCE"
    if s.roadmap_status == "completed" and not proven:
        return "KNOWN_NO_EVIDENCE"          # learned via roadmap, not yet proven
    if s.classification == "partial":
        return "PARTIAL"
    if s.classification == "transferable":
        return "TRANSFERABLE"
    return "NO_KNOWLEDGE"


# ---------------------------------------------------------------- 2. category

def action_category(state: str, ev_type: str, verifiable: bool) -> str:
    if state in ("NO_KNOWLEDGE", "TRANSFERABLE"):
        return "LEARN"
    if state == "PARTIAL":
        return "PRACTICE"
    if state == "KNOWN_NO_EVIDENCE":
        if ev_type == "problem_solving":
            return "PRACTICE"
        if ev_type in ("conceptual", "debugging"):
            return "PREPARE"
        if ev_type == "repository_practice":
            return "PROVE"                  # any repository shows it: never "build a project for Git"
        return "PROVE" if verifiable else "BUILD"
    return "PREPARE"                        # PROVEN


# ---------------------------------------------------------------- 3. priority

def progress_factor(s: SkillInput) -> float:
    if s.roadmap_status == "completed" and s.practical_done:
        return cfg.PROGRESS_COMPLETED_WITH_PRACTICAL
    return cfg.PROGRESS_FACTOR.get(s.roadmap_status, 0.0)


def prereqs(s: SkillInput) -> list[str]:
    """Module 5 roadmap prerequisites; the curated fallback only when the skill has no roadmap item."""
    if s.roadmap_item_id is not None or s.prerequisites:
        return s.prerequisites
    return catalog.KNOWN_PREREQUISITES.get(s.key, [])


def dependents_map(skills: list[SkillInput], states: dict[str, str]) -> dict[str, list[str]]:
    """skill key -> names of OPEN (not proven) skills whose roadmap prerequisites include it."""
    out: dict[str, list[str]] = {s.key: [] for s in skills}
    for s in skills:
        if states[s.key] == "PROVEN":
            continue
        for p in prereqs(s):
            if p in out and p != s.key:
                out[p].append(s.name)
    return out


def importance_factor(s: SkillInput, state: str) -> float:
    if state == "KNOWN_NO_EVIDENCE":
        return max(cfg.IMPORTANCE_FACTOR[s.m4_priority], cfg.EVIDENCE_IMPORTANCE_FACTOR[s.importance])
    return cfg.IMPORTANCE_FACTOR[s.m4_priority]


_UNLEARNED = ("NO_KNOWLEDGE", "TRANSFERABLE", "PARTIAL")


def blocked_by(skills: list[SkillInput], states: dict[str, str]) -> dict[str, list[str]]:
    """skill key -> names of its roadmap prerequisites that are still being learned. Such an action is ranked
    after its prerequisites (same rule as Module 6 next action: unblocked work first)."""
    names = {s.key: s.name for s in skills}
    return {s.key: [names[p] for p in prereqs(s)
                    if p in states and p != s.key and states[p] in _UNLEARNED]
            for s in skills}


def dependency_depth(skills: list[SkillInput], states: dict[str, str]) -> dict[str, int]:
    """Length of the longest chain of still-unlearned prerequisites below each skill
    (Python 0 -> FastAPI 1 -> Docker 2). Used to rank actions in a valid learning order. Cycle-safe."""
    pre = {s.key: [p for p in prereqs(s) if p in states and p != s.key and states[p] in _UNLEARNED]
               for s in skills}
    memo: dict[str, int] = {}

    def depth(k: str, seen: frozenset) -> int:
        if k in memo:
            return memo[k]
        d = max((1 + depth(p, seen | {k}) for p in pre.get(k, []) if p not in seen), default=0)
        memo[k] = d
        return d

    return {s.key: depth(s.key, frozenset()) for s in skills}


def priority_score(s: SkillInput, state: str, dependency: float) -> float:
    w = cfg.PRIORITY_WEIGHTS
    raw = (w["requirement"] * cfg.REQUIREMENT_FACTOR[s.importance]
           + w["severity"] * cfg.SEVERITY_FACTOR[state]
           + w["importance"] * importance_factor(s, state)
           + w["dependency"] * dependency
           + w["progress"] * (1 - progress_factor(s)))
    return round(100 * raw, 2)


def band(score: float) -> str:
    if score >= cfg.HIGH_THRESHOLD:
        return "HIGH"
    return "MEDIUM" if score >= cfg.MEDIUM_THRESHOLD else "LOW"


def apply_overrides(priority: str, s: SkillInput, state: str, n_dependents: int) -> tuple[str, list[str]]:
    codes = []
    if s.importance == "required" and state in ("NO_KNOWLEDGE", "TRANSFERABLE") and n_dependents > 0:
        if priority != "HIGH":
            codes.append("OVERRIDE_BLOCKING_GAP")
        priority = "HIGH"
    if s.importance == "optional" and priority != "LOW":
        codes.append("OVERRIDE_OPTIONAL_CAP")
        priority = "LOW"
    return priority, codes


# ---------------------------------------------------------------- reasons (deterministic WHY)

_STATE_TEXT = {
    "NO_KNOWLEDGE": "current gap",
    "TRANSFERABLE": "not yet learned (you have a related foundation)",
    "PARTIAL": "partially matched",
    "KNOWN_NO_EVIDENCE": "no solid evidence yet",
    "PROVEN": "already demonstrated",
}


def build_reason(s: SkillInput, state: str, dependents: list[str], verifiable: bool, category: str,
                 blockers: list[str] = ()) -> tuple[str, list[str]]:
    codes = [s.importance.upper(), state]
    parts = [f"{s.importance.capitalize()} skill for this role", _STATE_TEXT[state]]
    if s.m4_priority in ("high", "medium"):
        codes.append(f"M4_PRIORITY_{s.m4_priority.upper()}")
    if dependents:
        codes.append(f"BLOCKS:{len(dependents)}")
        parts.append(f"{', '.join(dependents[:3])} depend{'s' if len(dependents) == 1 else ''} on it")
    if blockers and category in ("LEARN", "PRACTICE"):
        codes.append("BLOCKED_BY:" + ",".join(b.lower() for b in blockers))
        parts.append(f"start after {', '.join(blockers[:3])}")
    if s.roadmap_status == "in_progress":
        codes.append("ROADMAP_IN_PROGRESS")
        parts.append("already in progress on your roadmap")
    if s.roadmap_status == "completed" and state == "KNOWN_NO_EVIDENCE" and s.classification != "strong":
        codes.append("ROADMAP_DONE_NO_EVIDENCE")
        parts.append("roadmap item completed, proof still missing")
    if s.evidence_adjusted:
        codes.append("EVIDENCE_ADJUSTED")
    if category == "PROVE" and verifiable:
        codes.append("AUTO_VERIFIABLE")
        parts.append("SkillGap AI can verify it from your repository")
    reason = parts[0] + " + " + " + ".join(parts[1:]) + "."
    return reason, codes


# ---------------------------------------------------------------- candidates

def _title_variant(s: SkillInput, state: str, category: str, ev_type: str) -> str:
    if category in ("LEARN", "PRACTICE") and s.roadmap_status in ("not_started", "in_progress"):
        return "roadmap"
    if category == "PRACTICE" and ev_type == "problem_solving":
        return "problem_solving"
    if category in ("BUILD", "PROVE"):
        return ev_type if ev_type in ("codebase", "deployable", "ai_pipeline", "frontend_ui",
                                      "repository_practice") else "codebase"
    if category == "PREPARE" and ev_type == "conceptual":
        return "conceptual"
    return "default"


def skill_candidates(inputs: CareerInputs) -> tuple[list[ActionCandidate], list[dict]]:
    skills = inputs.skills
    verifiable = set(inputs.verifiable_skills)
    states = {s.key: skill_state(s) for s in skills}
    deps = dependents_map(skills, states)
    blocks = blocked_by(skills, states)
    depths = dependency_depth(skills, states)
    max_deps = max((len(v) for v in deps.values()), default=0)

    cands, priorities = [], []
    for s in skills:
        state = states[s.key]
        if state == "PROVEN" and s.importance == "optional":
            continue                                    # nothing worth doing
        ev_type = catalog.evidence_type(s.key, s.category)
        can_verify = s.key in verifiable
        category = action_category(state, ev_type, can_verify)
        d = len(deps[s.key]) / max_deps if max_deps else 0.0
        score = priority_score(s, state, d)
        priority, override_codes = apply_overrides(band(score), s, state, len(deps[s.key]))
        reason, codes = build_reason(s, state, deps[s.key], can_verify, category, blocks[s.key])

        roadmap_done_variant = (category == "PROVE" and "ROADMAP_DONE_NO_EVIDENCE" in codes)
        variant = "roadmap_done" if roadmap_done_variant else _title_variant(s, state, category, ev_type)
        title = catalog.title_for(s.name, s.key, category, variant)
        ev_req = catalog.evidence_required(s.name, ev_type) if category in ("BUILD", "PROVE", "PRACTICE") else []

        c = ActionCandidate(
            action_key=f"{s.key}:{category}", category=category, priority=priority, priority_score=score,
            title=title, reason=reason, reason_codes=codes + override_codes, evidence_required=ev_req,
            skill_name=s.name, importance=s.importance, state=state, classification=s.classification,
            evidence_strength=round(s.evidence_strength, 2), job_requirement_id=s.job_requirement_id,
            gap_result_id=s.gap_result_id, roadmap_item_id=s.roadmap_item_id, roadmap_status=s.roadmap_status,
            depth=depths[s.key] if category in ("LEARN", "PRACTICE") else 0,
        )
        cands.append(c)
        priorities.append(dict(skill_name=s.name, importance=s.importance, classification=s.classification,
                               state=state, category=category, priority=priority, priority_score=score,
                               evidence_strength=round(s.evidence_strength, 2), reason=reason))
    return cands, priorities


def apply_candidates(inputs: CareerInputs, status: str) -> list[ActionCandidate]:
    """Job-search checklist, only once the profile is NEAR_READY or READY_TO_APPLY."""
    if status not in cfg.APPLY_SCORE:
        return []
    score = cfg.APPLY_SCORE[status]
    items = catalog.APPLY_CHECKLIST[: cfg.APPLY_ITEMS[status]]
    priority = band(score)
    reason = ("Your profile meets the Near Ready criteria for this role, so presenting your work becomes valuable."
              if status == "NEAR_READY" else
              "Your profile meets the Ready to Apply criteria for this role.")
    return [ActionCandidate(action_key=f"apply:{key}", category="APPLY", priority=priority, priority_score=score,
                            title=title.format(role=inputs.target_role), reason=reason,
                            reason_codes=[f"STATUS_{status}"], evidence_required=ev)
            for key, title, ev in items]


def _sort_key(c: ActionCandidate):
    momentum = 0 if c.roadmap_status == "in_progress" else 1
    return (_BAND_RANK[c.priority], c.depth, -c.priority_score, momentum,
            _IMPORTANCE_RANK.get(c.importance or "", 3), (c.skill_name or c.action_key).lower())


def build_plan(inputs: CareerInputs) -> EngineResult:
    from app.services.career.evidence_engine import evidence_gaps          # local: avoid import cycle
    from app.services.career.project_recommender import recommend

    cands, priorities = skill_candidates(inputs)
    cands, projects = recommend(cands)                                       # Step 5: merge BUILD -> projects
    status = evaluate_status(inputs)
    cands += apply_candidates(inputs, status.status)
    cands.sort(key=_sort_key)
    cands = cands[: cfg.MAX_ACTIONS]
    for i, c in enumerate(cands, start=1):
        c.rank = i
    kept = {c.action_key for c in cands}
    projects = [p for p in projects if p["action_key"] in kept]
    priorities.sort(key=lambda p: (_BAND_RANK[p["priority"]], -p["priority_score"], p["skill_name"].lower()))
    return EngineResult(status=status, actions=cands, skill_priorities=priorities, projects=projects,
                        evidence_gaps=evidence_gaps(inputs, cands))
