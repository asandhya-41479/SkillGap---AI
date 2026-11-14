"""Module 7 Step 5: evidence checklist + project recommendations (pure, no DB / Gemini)."""
from app.schemas.career import EvidenceRef
from app.services.career import catalog
from app.services.career.action_engine import build_plan
from .test_action_engine import by_skill, inputs, scenario_a, scenario_b, scenario_c, sk


def ev(source, kind, strength, status=None, url="https://github.com/u/repo"):
    return EvidenceRef(source=source, kind=kind, strength=strength, status=status, url=url)


def projects_of(plan):
    return {p["blueprint_id"]: p for p in plan.projects}


# ------------------------------------------------------------------ projects: only when they close a real gap
def test_no_projects_for_strong_profile_extend_existing_repo_instead():
    plan = build_plan(scenario_a())
    assert plan.projects == []
    assert by_skill(plan)["Docker"].category == "PROVE"          # prove in SkillGap AI, no new project


def test_no_projects_for_beginner_learn_first():
    plan = build_plan(scenario_b())
    assert plan.projects == [] and not any(a.action_key.startswith("project:") for a in plan.actions)


def test_project_for_unprovable_skill_replaces_skill_build_action():
    plan = build_plan(scenario_c())
    proj = projects_of(plan)
    assert list(proj) == ["knowledge-assistant"]
    assert proj["knowledge-assistant"]["skills_covered"] == ["RAG"]
    keys = [a.action_key for a in plan.actions]
    assert "project:knowledge-assistant" in keys and "rag:BUILD" not in keys     # merged, not duplicated
    act = next(a for a in plan.actions if a.action_key == "project:knowledge-assistant")
    assert act.category == "BUILD" and act.priority == "HIGH"
    assert "ROADMAP_DONE_NO_EVIDENCE" in act.reason_codes                        # member WHY preserved
    assert "Architecture diagram" in " ".join(act.evidence_required) or act.evidence_required


def test_one_project_covers_several_gaps():
    i = inputs([
        sk("RAG", "required", "strong", strength=0.25, category="ai_ml"),
        sk("LLM", "required", "strong", strength=0.25, category="ai_ml"),
        sk("Prompt Engineering", "preferred", "strong", strength=0.0, category="ai_ml"),
        sk("Python", "required", "strong", strength=1.0, category="programming_language"),
    ], score=70)
    plan = build_plan(i)
    assert list(projects_of(plan)) == ["knowledge-assistant"]
    assert set(projects_of(plan)["knowledge-assistant"]["skills_covered"]) == {"RAG", "LLM", "Prompt Engineering"}
    assert sum(a.action_key.startswith("project:") for a in plan.actions) == 1


def test_at_most_max_projects():
    skills = [sk(n, "required", "strong", strength=0.0, category=c) for n, c in [
        ("RAG", "ai_ml"), ("Machine Learning", "ai_ml"), ("Tableau", "tool"), ("Flutter", "framework"),
        ("Kafka", "tool"), ("Socket.IO", "library")]]
    plan = build_plan(inputs(skills, score=60))
    assert 1 <= len(plan.projects) <= catalog.MAX_PROJECTS


def test_projects_are_from_the_curated_catalog_only():
    ids = {b["id"] for b in catalog.PROJECT_BLUEPRINTS}
    for f in (scenario_a, scenario_b, scenario_c):
        assert {p["blueprint_id"] for p in build_plan(f()).projects} <= ids


def test_uncovered_build_skill_keeps_generic_build_action():
    plan = build_plan(inputs([sk("Quantum Widgets", "required", "strong", strength=0.0, category="ai_ml")], score=50))
    assert plan.projects == [] and plan.actions[0].action_key == "quantum widgets:BUILD"


# ------------------------------------------------------------------ evidence checklist
def test_evidence_gap_rows_link_to_actions():
    plan = build_plan(scenario_c())
    gaps = {g["skill_name"]: g for g in plan.evidence_gaps}
    assert gaps["RAG"]["recommended_action_key"] == "project:knowledge-assistant"
    assert gaps["Docker"]["recommended_action_key"] == "docker:PROVE"
    assert "SQL" not in gaps                                                     # proven skills are not gaps
    for g in plan.evidence_gaps:
        assert g["required_evidence"] and g["missing_evidence"]


def test_current_evidence_is_never_invented():
    plan = build_plan(scenario_c())
    for g in plan.evidence_gaps:
        assert g["current_evidence"] == []                                       # scenario has no evidence rows


def test_missing_evidence_explains_weak_evidence():
    cases = [
        (ev("progress_evidence", "project_url", 0.40, "linked"), "project link is accepted but not verified"),
        (ev("progress_evidence", "github_repo", 0.25, "unverified"), "Code in the attached repository"),
        (ev("github_detected", "topic", 0.25), "topic tag is only a label"),
        (ev("roadmap", "completed_item", 0.25, url=None), "shows learning, not proof"),
    ]
    for ref, phrase in cases:
        s = sk("Docker", "required", "strong", strength=ref.strength, category="devops")
        s.evidence = [ref]
        gap = build_plan(inputs([s], score=50)).evidence_gaps[0]
        assert phrase in " ".join(gap["missing_evidence"]), (ref.kind, gap["missing_evidence"])


def test_solid_evidence_but_old_gap_classification_asks_for_reanalysis():
    s = sk("Docker", "required", "gap", strength=1.0, category="devops")      # verified repo, Module 4 not re-run
    s.evidence = [ev("progress_evidence", "github_repo", 1.0, "verified")]
    gap = build_plan(inputs([s], score=50)).evidence_gaps[0]
    assert "Re-run the Skill Gap Analysis" in gap["missing_evidence"][0]


def test_verification_hint_shows_what_skillgap_checks():
    i = scenario_a()
    i.verification_hints = {"docker": "dockerfile or docker-compose.yml in the repository root"}
    gap = {g["skill_name"]: g for g in build_plan(i).evidence_gaps}["Docker"]
    assert any("dockerfile" in r for r in gap["required_evidence"])


def test_optional_and_proven_skills_not_listed():
    plan = build_plan(inputs([sk("Kubernetes", "optional", "gap", category="devops"),
                              sk("Python", "required", "strong", strength=1.0)], score=60))
    assert plan.evidence_gaps == []
