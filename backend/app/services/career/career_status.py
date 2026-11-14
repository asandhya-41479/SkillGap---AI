"""Module 7: Career Status (explainable, rule-based, never a hiring guarantee). Pure: no DB, no Gemini.

Metrics (computed on the role's CORE skills = required skills; if the job lists none as required, preferred
skills are used, and if none of those, all skills, so the status still works for loosely written job posts):
  R  % core skills classified strong by Module 4
  C  number of core skills still a gap/transferable (critical gaps)
  E  % core skills with solid evidence (Module 6 strength >= PROVEN_THRESHOLD)
  P  roadmap completion % (Module 5). No active roadmap -> not applicable, the criterion is skipped
  Q  % HIGH-priority interview topics prepared (Module 7 Step 6). Not generated yet -> counts as not met
  S  Career Readiness score (Module 6). "Not enough data" -> counts as not met
Rules are evaluated top-down: READY_TO_APPLY, NEAR_READY, DEVELOPING (any one of R/S), else BUILDING_FOUNDATION.
"""
from dataclasses import dataclass, field

from app.core import career_config as cfg
from app.schemas.career import CareerInputs

ORDER = ["BUILDING_FOUNDATION", "DEVELOPING", "NEAR_READY", "READY_TO_APPLY"]


@dataclass
class StatusResult:
    status: str
    metrics: dict
    criteria: list[dict]                 # all metrics checked against READY_TO_APPLY (the end goal)
    next_status: dict | None = None      # next level up: which criteria are met / missing
    core_basis: str = "required"
    notes: list[str] = field(default_factory=list)


def core_skills(inputs: CareerInputs):
    for imp in ("required", "preferred"):
        core = [s for s in inputs.skills if s.importance == imp]
        if core:
            return core, imp
    return list(inputs.skills), "all"


def compute_metrics(inputs: CareerInputs) -> tuple[dict, str]:
    core, basis = core_skills(inputs)
    n = len(core)
    pct = lambda k: round(100 * k / n, 1) if n else None  # noqa: E731
    metrics = {
        "R": pct(sum(s.classification == "strong" for s in core)),
        "C": sum(s.classification in ("gap", "transferable") for s in core) if n else None,
        "E": pct(sum(s.evidence_strength >= cfg.PROVEN_THRESHOLD for s in core)),
        "P": inputs.roadmap_pct,
        "Q": inputs.interview_prep_pct,
        "S": inputs.readiness.score,
    }
    return metrics, basis


def _check(key: str, rule: tuple[str, float], value) -> dict:
    op, threshold = rule
    if value is None:
        met = key == "P"          # no roadmap: nothing left to learn on it, criterion not applicable
    else:
        met = value >= threshold if op == ">=" else value <= threshold
    return dict(key=key, label=cfg.STATUS_LABELS[key], value=value, threshold=threshold, comparator=op, met=met)


def _rule_met(rules: dict, metrics: dict) -> tuple[bool, list[dict]]:
    checks = [_check(k, r, metrics[k]) for k, r in rules.items()]
    return all(c["met"] for c in checks), checks


def evaluate_status(inputs: CareerInputs) -> StatusResult:
    metrics, basis = compute_metrics(inputs)
    status = None
    for name, rules in cfg.STATUS_RULES:
        ok, _ = _rule_met(rules, metrics)
        if ok:
            status = name
            break
    if status is None:
        dev = [_check(k, r, metrics[k]) for k, r in cfg.DEVELOPING_RULE.items()]
        status = "DEVELOPING" if any(c["met"] and c["value"] is not None for c in dev) else "BUILDING_FOUNDATION"

    _, goal = _rule_met(dict(cfg.STATUS_RULES)["READY_TO_APPLY"], metrics)

    nxt = None
    idx = ORDER.index(status)
    if idx < len(ORDER) - 1:
        target = ORDER[idx + 1]
        if target == "DEVELOPING":
            checks = [_check(k, r, metrics[k]) for k, r in cfg.DEVELOPING_RULE.items()]
            met = int(any(c["met"] for c in checks))
            nxt = dict(status=target, met=met, total=1, criteria=checks)
        else:
            _, checks = _rule_met(dict(cfg.STATUS_RULES)[target], metrics)
            nxt = dict(status=target, met=sum(c["met"] for c in checks), total=len(checks), criteria=checks)

    notes = []
    if basis != "required":
        notes.append(f"No required skills were found in this job description, so {basis} skills were used as core skills.")
    if metrics["Q"] is None:
        notes.append("Interview preparation has not been generated yet.")
    if metrics["S"] is None:
        notes.append("Career Readiness has not enough data yet.")
    return StatusResult(status=status, metrics=metrics, criteria=goal, next_status=nxt, core_basis=basis, notes=notes)
