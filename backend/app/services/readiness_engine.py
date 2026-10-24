"""Module 6 Step 5: the Career Readiness formula. Pure and deterministic: no database, no network, no Gemini.

Career Readiness is an explainable estimate of how well the user's CURRENT evidence matches one job. It is not
a hiring probability. Components, each in [0, 1] (weight w = Module 4 importance weight, credit c = Module 4
classification credit):
  alignment          A = sum(w*c) / sum(w)                       same as Module 4's alignment score
  required_coverage  C = required skills classified strong / required skills
  evidence           E = sum(w * demonstrated) / sum(w)          demonstrated = best evidence strength of the skill
  gap_health         G = 1 - sum(w of high-priority gaps) / sum(w)
  roadmap            P = roadmap completion (only when a roadmap exists for this analysis)
A component that cannot be computed is dropped and the remaining weights are re-normalised.
Roadmap progress and evidence feed ONLY E and P: they never change a classification or a skill level.
"""
from dataclasses import dataclass

from app.core import readiness_config as cfg
from app.core.skill_gap_config import CLASSIFICATION_CREDIT, IMPORTANCE_WEIGHT
from app.models.job import Importance
from app.models.skill_gap import MatchClassification as M, PriorityLevel
from app.services.github_evidence import skill_key


@dataclass(frozen=True)
class Req:
    skill: str
    importance: Importance
    classification: M
    priority: PriorityLevel


def label_for(score: float | None) -> str:
    return cfg.NOT_ENOUGH_DATA if score is None else next(t for cap, t in cfg.LABELS if score < cap)


def compute(reqs: list[Req], strengths: dict[str, float], roadmap_pct: float | None) -> dict:
    """roadmap_pct is 0-100 or None. Returns score/label/components/weights/metrics/breakdown."""
    total = sum(IMPORTANCE_WEIGHT[r.importance] for r in reqs)
    required = [r for r in reqs if r.importance == Importance.required]
    demo = {r.skill: min(1.0, max(0.0, strengths.get(skill_key(r.skill), 0.0))) for r in reqs}
    w = lambda r: IMPORTANCE_WEIGHT[r.importance]  # noqa: E731

    comps = {
        "alignment": sum(w(r) * CLASSIFICATION_CREDIT[r.classification] for r in reqs) / total if total else None,
        "required_coverage": sum(r.classification == M.strong for r in required) / len(required) if required else None,
        "evidence": sum(w(r) * demo[r.skill] for r in reqs) / total if total else None,
        "gap_health": 1 - sum(w(r) for r in reqs if r.priority == PriorityLevel.high) / total if total else None,
        "roadmap": None if roadmap_pct is None else roadmap_pct / 100,
    }
    metrics = {
        "alignment_pct": None if comps["alignment"] is None else round(comps["alignment"] * 100, 2),
        **{c.value: sum(r.classification == c for r in reqs) for c in M},
        "required_total": len(required), "required_covered": sum(r.classification == M.strong for r in required),
        "high_priority_open": sum(r.priority == PriorityLevel.high for r in reqs), "roadmap_pct": roadmap_pct,
    }
    breakdown = [dict(skill_name=r.skill, importance=r.importance.value, classification=r.classification.value,
                      priority=r.priority.value, weight=w(r), credit=CLASSIFICATION_CREDIT[r.classification],
                      evidence_strength=round(demo[r.skill], 2)) for r in reqs]

    live = {k: v for k, v in comps.items() if v is not None}
    enough = len(reqs) >= cfg.MIN_REQUIREMENTS and total > 0
    wsum = sum(cfg.COMPONENT_WEIGHTS[k] for k in live)
    weights = {k: round(cfg.COMPONENT_WEIGHTS[k] / wsum, 4) for k in live} if enough else {}
    score = round(100 * sum(cfg.COMPONENT_WEIGHTS[k] * v for k, v in live.items()) / wsum, 2) if enough else None
    return dict(score=score, label=label_for(score), weights=weights, metrics=metrics, breakdown=breakdown,
                components={k: None if v is None else round(v, 4) for k, v in comps.items()})