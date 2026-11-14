"""Module 7 Step 5: evidence checklist. Pure and deterministic.

For every required/preferred skill that is not yet PROVEN:
  Skill -> Required evidence -> Current evidence -> Missing evidence -> Recommended action

- Required evidence comes from the catalog (by evidence type) plus, when Module 6 can verify the skill, the
  exact repository signal it looks for (from github_evidence.SIGNALS), so the advice matches what the
  system can actually check.
- Current evidence is what Modules 2/5/6 already hold (never invented, strength computed by Module 6).
- Missing evidence explains the gap between the two, using the same strength rules as Module 6
  (project link 0.40 < 0.60, unverified repo 0.25, learning only 0.25, topic tag 0.25).
"""
from app.core import career_config as cfg
from app.schemas.career import CareerInputs, SkillInput
from app.services.career import catalog
from app.services.career.action_engine import skill_state


def _missing(s: SkillInput, required: list[str], hint: str | None) -> list[str]:
    if s.evidence_strength >= cfg.PROVEN_THRESHOLD:
        # evidence is solid but Module 4 still shows a gap/partial: its classification is older than the proof
        return ["Re-run the Skill Gap Analysis so your new evidence is reflected in this role's match"]
    if not s.evidence:
        return required
    best = max(s.evidence, key=lambda e: e.strength)
    signal = f" ({hint})" if hint else ""
    if best.source == "roadmap":
        return [f"Project evidence for {s.name}: a completed roadmap item shows learning, not proof"] + required
    if best.kind == "project_url":
        return [f"A GitHub repository you own that uses {s.name}{signal}: a project link is accepted but not verified"]
    if best.kind == "github_repo" and best.status == "unverified":
        return [f"A {s.name} signal in the attached repository{signal}"] if hint else \
               [f"Code in the attached repository that clearly uses {s.name}"]
    if best.kind == "topic":
        return [f"Code that uses {s.name}: a repository topic tag is only a label{signal}"]
    return [f"Stronger evidence for {s.name}{signal}"]


def evidence_gaps(inputs: CareerInputs, actions: list) -> list[dict]:
    """actions: final ranked ActionCandidates (used to link each gap to its recommended action)."""
    by_skill: dict[str, object] = {}
    for a in actions:                                    # first (highest ranked) action for a skill wins
        if not a.skill_name:
            continue
        for k in (a.covers or [a.action_key.split(":", 1)[0]]):
            by_skill.setdefault(k, a)

    gaps = []
    for s in inputs.skills:
        if s.importance == "optional" or skill_state(s) == "PROVEN":
            continue
        ev_type = catalog.evidence_type(s.key, s.category)
        hint = inputs.verification_hints.get(s.key)
        required = catalog.evidence_required(s.name, ev_type)
        if hint:
            required = required + [f"Signal SkillGap AI can verify: {hint}"]
        act = by_skill.get(s.key)
        gaps.append(dict(
            skill_name=s.name, importance=s.importance, required_evidence=required,
            current_evidence=[e.model_dump() for e in s.evidence],
            missing_evidence=_missing(s, catalog.evidence_required(s.name, ev_type), hint),
            recommended_action_key=act.action_key if act else None,
            recommended_action_title=act.title if act else None,
            _rank=act.rank if act else 10_000,
        ))
    gaps.sort(key=lambda g: (g["_rank"], g["importance"] != "required", g["skill_name"].lower()))
    for g in gaps:
        g.pop("_rank")
    return gaps
