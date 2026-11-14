"""Module 7 Step 3: deterministic Career Action Engine with realistic profiles (pure, no DB / Gemini)."""
import pytest

from app.schemas.career import CareerInputs, SkillInput
from app.services.career.action_engine import (
    action_category,
    build_plan,
    priority_score,
    skill_state,
)

# Module 4 PRIORITY_TABLE (app/core/skill_gap_config.py) as plain strings, so this file needs no database
PRIORITY = {
    ("required", "gap"): "high", ("required", "transferable"): "high",
    ("required", "partial"): "medium", ("required", "strong"): "none",
    ("preferred", "gap"): "medium", ("preferred", "transferable"): "low",
    ("preferred", "partial"): "low", ("preferred", "strong"): "none",
    ("optional", "gap"): "low", ("optional", "transferable"): "low",
    ("optional", "partial"): "low", ("optional", "strong"): "none",
}

VERIFIABLE = ["docker", "fastapi", "sql", "postgresql", "python", "aws", "react", "pytest"]


def sk(name, importance, classification, priority=None, strength=0.0, category="framework",
       roadmap=None, practical=False, prereq=(), item_id=None):
    return SkillInput(name=name, key=name.lower(), category=category, importance=importance,
                      classification=classification,
                      m4_priority=priority or PRIORITY[(importance, classification)],
                      evidence_strength=strength, roadmap_status=roadmap, practical_done=practical,
                      prerequisites=list(prereq), roadmap_item_id=item_id)


def inputs(skills, score, roadmap_pct=None, prep=None):
    return CareerInputs(user_id=1, analysis_id=10, job_description_id=5, target_role="AI Engineer",
                        readiness={"score": score}, roadmap_pct=roadmap_pct, interview_prep_pct=prep,
                        verifiable_skills=VERIFIABLE, skills=skills)


def by_skill(plan):
    return {a.skill_name: a for a in plan.actions if a.skill_name}


# ------------------------------------------------------------------ Scenario A: strong skills, few gaps
def scenario_a(prep=40):
    return inputs([
        sk("Python", "required", "strong", strength=1.0, category="programming_language"),
        sk("FastAPI", "required", "strong", strength=1.0),
        sk("SQL", "required", "strong", strength=0.6, category="database"),
        sk("RAG", "required", "strong", strength=1.0, category="ai_ml"),
        sk("Docker", "required", "strong", strength=0.25, category="devops"),     # knows it, no proof
        sk("AWS", "preferred", "gap", category="cloud"),
    ], score=82, roadmap_pct=85, prep=prep)


def test_scenario_a_strong_profile():
    plan = build_plan(scenario_a())
    acts = by_skill(plan)
    assert plan.status.status == "NEAR_READY"                       # READY blocked by Q (40 < 60) and E
    assert acts["Docker"].category == "PROVE"                        # verifiable from repo files
    assert "AUTO_VERIFIABLE" in acts["Docker"].reason_codes
    assert acts["AWS"].category == "LEARN"
    assert acts["Python"].category == "PREPARE"                      # proven -> interview prep
    assert sum(a.category == "APPLY" for a in plan.actions) == 2     # NEAR_READY: short checklist only
    # proving a REQUIRED skill outranks learning a PREFERRED one
    assert plan.actions[0].skill_name == "Docker" and plan.actions[0].priority == "HIGH"
    # nothing tells a strong user to "learn" a required skill
    assert not [a for a in plan.actions if a.category == "LEARN" and a.importance == "required"]


def test_scenario_a_ready_to_apply_when_prep_done():
    i = scenario_a(prep=80)
    i.skills[4].evidence_strength = 1.0                              # Docker repo verified
    plan = build_plan(i)
    assert plan.status.status == "READY_TO_APPLY"
    assert plan.status.next_status is None
    apply = [a for a in plan.actions if a.category == "APPLY"]
    assert len(apply) == 4 and all(a.priority == "HIGH" for a in apply)


# ------------------------------------------------------------------ Scenario B: moderate, several critical gaps
def scenario_b():
    return inputs([
        sk("Python", "required", "partial", category="programming_language", roadmap="in_progress", item_id=1),
        sk("SQL", "required", "strong", strength=0.6, category="database"),
        sk("FastAPI", "required", "transferable", prereq=["python"], roadmap="not_started", item_id=2),
        sk("Embeddings", "required", "gap", category="ai_ml", prereq=["python"], roadmap="not_started", item_id=3),
        sk("RAG", "required", "gap", category="ai_ml", prereq=["embeddings", "python"], roadmap="not_started", item_id=4),
        sk("Docker", "required", "gap", category="devops", prereq=["fastapi"], roadmap="not_started", item_id=5),
        sk("DSA", "preferred", "partial", category="concept"),
    ], score=41, roadmap_pct=10)


def test_scenario_b_many_gaps():
    plan = build_plan(scenario_b())
    acts = by_skill(plan)
    assert plan.status.status == "DEVELOPING"                         # S=41 >= 40 (approved "or" rule)
    assert plan.status.metrics["C"] == 4
    assert acts["Python"].category == "PRACTICE"
    for s in ("FastAPI", "Embeddings", "RAG", "Docker"):
        assert acts[s].category == "LEARN"
        assert acts[s].priority == "HIGH"
    assert not any(a.category in ("BUILD", "APPLY") for a in plan.actions)   # too early to build or apply
    assert acts["Python"].reason_codes.count("BLOCKS:3") == 1        # FastAPI, Embeddings, RAG depend on it
    assert "roadmap" in acts["FastAPI"].title.lower()                 # points at the existing roadmap milestone
    # learning order respects prerequisites: Python (foundation, unblocked) first, Docker after FastAPI
    keys = [a.action_key for a in plan.actions]
    assert keys[0] == "python:PRACTICE"
    assert keys.index("fastapi:LEARN") < keys.index("docker:LEARN")
    assert keys.index("embeddings:LEARN") < keys.index("rag:LEARN") or \
        acts["RAG"].priority_score <= acts["Embeddings"].priority_score
    assert any(c.startswith("BLOCKED_BY:") for c in acts["Docker"].reason_codes)
    assert "start after FastAPI" in acts["Docker"].reason


# ------------------------------------------------------------------ Scenario C: strong learning, weak evidence
def scenario_c():
    return inputs([
        sk("Python", "required", "strong", strength=0.25, category="programming_language", roadmap="completed"),
        sk("FastAPI", "required", "strong", strength=0.25, roadmap="completed"),
        sk("RAG", "required", "gap", category="ai_ml", roadmap="completed", priority="high"),
        sk("Docker", "required", "partial", category="devops", roadmap="completed"),
        sk("SQL", "required", "strong", strength=0.6, category="database"),
        sk("AWS", "preferred", "gap", category="cloud"),
    ], score=63, roadmap_pct=80)


def test_scenario_c_learning_without_evidence():
    plan = build_plan(scenario_c())
    acts = by_skill(plan)
    assert plan.status.status == "DEVELOPING"                         # NEAR_READY blocked by evidence/coverage
    assert plan.status.next_status["status"] == "NEAR_READY"
    assert acts["RAG"].category == "BUILD"                             # not verifiable from files -> build project
    assert "ROADMAP_DONE_NO_EVIDENCE" in acts["RAG"].reason_codes
    assert acts["Docker"].category == "PROVE"                         # roadmap done -> prove it
    assert acts["FastAPI"].category == "PROVE"
    proof = [a for a in plan.actions if a.category in ("BUILD", "PROVE")]
    assert len(proof) >= 4                                             # the plan is about producing evidence
    assert not [a for a in plan.actions if a.category == "LEARN" and a.importance == "required"]


def test_scenarios_produce_different_plans():
    cats = lambda p: sorted({a.category for a in p.actions[:5]})  # noqa: E731
    a, b, c = (build_plan(x()) for x in (scenario_a, scenario_b, scenario_c))
    assert len({tuple(cats(a)), tuple(cats(b)), tuple(cats(c))}) == 3


# ------------------------------------------------------------------ rules
@pytest.mark.parametrize("cls,strength,roadmap,expected", [
    ("gap", 0, None, "NO_KNOWLEDGE"),
    ("transferable", 0, None, "TRANSFERABLE"),
    ("partial", 0, None, "PARTIAL"),
    ("strong", 0.4, None, "KNOWN_NO_EVIDENCE"),      # project link only (0.40) is not proof
    ("strong", 0.6, None, "PROVEN"),
    ("gap", 0.25, "completed", "KNOWN_NO_EVIDENCE"),
    ("gap", 1.0, "completed", "NO_KNOWLEDGE"),       # proven evidence but Module 4 not re-run: still a gap there
])
def test_skill_state(cls, strength, roadmap, expected):
    s = sk("X", "required", cls, strength=strength, roadmap=roadmap)
    assert skill_state(s) == expected


@pytest.mark.parametrize("state,ev,verifiable,expected", [
    ("NO_KNOWLEDGE", "codebase", True, "LEARN"),
    ("PARTIAL", "codebase", True, "PRACTICE"),
    ("KNOWN_NO_EVIDENCE", "deployable", True, "PROVE"),
    ("KNOWN_NO_EVIDENCE", "ai_pipeline", False, "BUILD"),
    ("KNOWN_NO_EVIDENCE", "problem_solving", False, "PRACTICE"),
    ("KNOWN_NO_EVIDENCE", "conceptual", False, "PREPARE"),
    ("PROVEN", "codebase", True, "PREPARE"),
])
def test_action_category(state, ev, verifiable, expected):
    assert action_category(state, ev, verifiable) == expected


def test_priority_formula_values():
    # required gap, high, no deps, no progress = 100*(.35+.25+.20+0+.10) = 90
    assert priority_score(sk("X", "required", "gap"), "NO_KNOWLEDGE", 0) == 90.0
    # preferred partial, low = 100*(.175+.15+.06+0+.10) = 48.5
    assert priority_score(sk("X", "preferred", "partial"), "PARTIAL", 0) == 48.5
    # required strong but unproven: I = evidence factor 0.6 -> 100*(.35+.10+.12+0+.10) = 67 (HIGH)
    assert priority_score(sk("X", "required", "strong", strength=0.25), "KNOWN_NO_EVIDENCE", 0) == 67.0


def test_proving_required_beats_learning_preferred():
    plan = build_plan(inputs([sk("Docker", "required", "strong", strength=0.4, category="devops"),
                              sk("AWS", "preferred", "gap", category="cloud")], score=70))
    assert [a.skill_name for a in plan.actions] == ["Docker", "AWS"]


def test_optional_skills_capped_low():
    plan = build_plan(inputs([sk("Kubernetes", "optional", "gap", category="devops"),
                              sk("Python", "required", "strong", strength=1.0)], score=60))
    k = by_skill(plan)["Kubernetes"]
    assert k.priority == "LOW" and "OVERRIDE_OPTIONAL_CAP" in k.reason_codes


def test_one_action_per_skill_and_stable_keys():
    plan = build_plan(scenario_b())
    keys = [a.action_key for a in plan.actions]
    assert len(keys) == len(set(keys))
    assert "docker:LEARN" in keys
    assert build_plan(scenario_b()).actions[0].action_key == plan.actions[0].action_key   # deterministic


def test_ranks_are_sequential_and_sorted_by_priority():
    plan = build_plan(scenario_b())
    assert [a.rank for a in plan.actions] == list(range(1, len(plan.actions) + 1))
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    assert [order[a.priority] for a in plan.actions] == sorted(order[a.priority] for a in plan.actions)


def test_actions_only_for_real_requirements():
    plan = build_plan(scenario_b())
    names = {s.name for s in scenario_b().skills}
    assert {a.skill_name for a in plan.actions if a.skill_name} <= names


def test_apply_never_names_companies_or_jobs():
    plan = build_plan(scenario_a())
    for a in plan.actions:
        if a.category == "APPLY":
            assert "AI Engineer" in a.title or "README" in a.title or "STAR" in a.title or "repositories" in a.title
            assert "salary" not in a.title.lower() and "http" not in a.title


def test_empty_profile_is_building_foundation():
    plan = build_plan(inputs([], score=None))
    assert plan.status.status == "BUILDING_FOUNDATION"
    assert plan.actions == []


def test_core_falls_back_to_preferred_when_no_required():
    plan = build_plan(inputs([sk("Python", "preferred", "strong", strength=1.0),
                              sk("Docker", "preferred", "gap", category="devops")], score=50))
    assert plan.status.core_basis == "preferred"
    assert plan.status.metrics["R"] == 50.0


def test_no_roadmap_skips_progress_criterion():
    i = scenario_a(prep=80); i.roadmap_pct = None; i.skills[4].evidence_strength = 1.0
    assert build_plan(i).status.status == "READY_TO_APPLY"
