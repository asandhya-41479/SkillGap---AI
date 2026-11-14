"""Module 7 Step 5: project recommendations. Pure and deterministic.

Rules (approved design):
1. Prefer proving in an EXISTING project: skills Module 6 can verify from repository files already get PROVE
   actions ("add Docker to your repo"). Only skills whose action is BUILD (need a new project) are "anchors".
2. Pick blueprints by greedy weighted set cover over the anchors: required anchor = 2, preferred = 1,
   optional = 0.5, plus 0.25 for every other open skill of this role the project also exercises.
   A blueprint qualifies only if it covers at least one still-uncovered anchor.
3. At most MAX_PROJECTS; none when there are no anchors (e.g. a beginner who still has to LEARN first).
4. Each chosen project REPLACES the per-skill BUILD actions it covers with one tracked BUILD action
   ("project:<id>"), so the user sees one clear project instead of several overlapping ones.
An anchor no blueprint covers keeps its generic per-skill BUILD action.
"""
from app.services.career import catalog
from app.services.career.action_engine import ActionCandidate

_W = {"required": 2.0, "preferred": 1.0, "optional": 0.5}
_BONUS = 0.25
_BAND_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _key(c: ActionCandidate) -> str:
    return c.action_key.split(":", 1)[0]


def recommend(cands: list[ActionCandidate]) -> tuple[list[ActionCandidate], list[dict]]:
    """Returns (actions with project actions merged in, project recommendations for the plan)."""
    anchors = {_key(c): c for c in cands if c.category == "BUILD" and c.skill_name}
    open_names = {_key(c): c.skill_name for c in cands if c.skill_name and c.state != "PROVEN"}
    open_skills = set(open_names)
    if not anchors:
        return cands, []

    uncovered = set(anchors)
    chosen = []
    while uncovered and len(chosen) < catalog.MAX_PROJECTS:
        best, best_score = None, 0.0
        for bp in catalog.PROJECT_BLUEPRINTS:
            if any(bp["id"] == b["id"] for b, _ in chosen):
                continue
            hit = bp["skills"] & uncovered
            if not hit:
                continue
            score = sum(_W.get(anchors[k].importance, 0.5) for k in hit) \
                + _BONUS * len((bp["skills"] & open_skills) - hit)
            if score > best_score:                      # strict ">" keeps catalog order on ties
                best, best_score = bp, score
        if best is None:
            break
        hit = best["skills"] & uncovered
        chosen.append((best, hit))
        uncovered -= hit

    merged_keys, project_actions, projects = set(), [], []
    for bp, hit in chosen:
        members = sorted((anchors[k] for k in hit),
                         key=lambda c: (_BAND_RANK[c.priority], -c.priority_score, c.skill_name.lower()))
        lead = members[0]
        also = sorted(open_names[k] for k in (bp["skills"] & open_skills) - hit)
        names = [m.skill_name for m in members]
        detail = "; ".join(f"{m.skill_name} ({m.importance}, no solid evidence yet)" for m in members)
        action = ActionCandidate(
            action_key=f"project:{bp['id']}", category="BUILD", priority=lead.priority,
            priority_score=max(m.priority_score for m in members),
            title=f"Build the {bp['name']} project to prove {', '.join(names)}",
            reason=f"One project proves {len(members)} skill{'s' if len(members) > 1 else ''} this role needs: {detail}.",
            reason_codes=["PROJECT", "COVERS:" + ",".join(sorted(hit))]
            + list(dict.fromkeys(code for m in members for code in m.reason_codes)),   # keep the members' WHY
            evidence_required=list(bp["artifacts"]), skill_name=lead.skill_name, importance=lead.importance,
            state=lead.state, classification=lead.classification, evidence_strength=lead.evidence_strength,
            job_requirement_id=lead.job_requirement_id, gap_result_id=lead.gap_result_id,
            roadmap_item_id=lead.roadmap_item_id, roadmap_status=lead.roadmap_status, covers=sorted(hit),
        )
        project_actions.append(action)
        merged_keys |= {m.action_key for m in members}
        projects.append(dict(blueprint_id=bp["id"], name=bp["name"], purpose=bp["purpose"],
                             skills_covered=names, also_practises=also,
                             evidence_artifacts=list(bp["artifacts"]), description=None,
                             action_key=action.action_key))

    kept = [c for c in cands if c.action_key not in merged_keys]
    return kept + project_actions, projects
