"""Deterministic roadmap rule engine (Module 5, Step 3).

Pure functions: no database, no Gemini. Input is verified Module 4 data plus the user's
constraints; output is a "skeleton" plan. Gemini (Step 4) may only fill in wording for the
items produced here — it can never add, remove, reorder or re-prioritise them.

Pipeline:
  filter gaps -> add hard prerequisites -> order (Kahn + priority key) -> time-fit -> weeks
"""
import heapq
import math
from dataclasses import dataclass, field

from app.core.roadmap_config import (
    CAPACITY_TOLERANCE,
    CLASSIFICATION_RANK,
    IMPORTANCE_RANK,
    NOTE_NO_GAPS,
    NOTE_TIGHT_PLAN,
    NOTE_TIME_INSUFFICIENT,
    PRIORITY_RANK,
    TIGHT_PLAN_UTILISATION,
)
from app.models.job import Importance
from app.models.roadmap import EffortSize
from app.models.skill_gap import MatchClassification, PriorityLevel
from app.services.roadmap.dependency_graph import display_name, hard_prereqs, skill_key, soft_prereqs
from app.services.roadmap.effort import base_size, estimate_hours, reduced_hours
from app.services.roadmap.plan_types import (
    GapInput,
    PlanInput,
    PlannedItem,
    RoadmapConstraints,
    RulePlan,
)

_RANK_TO_PRIORITY = {v: k for k, v in PRIORITY_RANK.items()}


@dataclass
class _Node:
    key: str
    name: str
    gap: GapInput | None            # None => supplementary prerequisite
    priority_rank: int              # displayed priority rank (inherited for supplementary)
    effective_rank: int = 0         # ordering-only rank (inherits from dependents)
    size: EffortSize = EffortSize.medium
    hours: float = 0.0
    hard: set[str] = field(default_factory=set)   # in-plan hard prerequisites
    soft: set[str] = field(default_factory=set)   # in-plan soft prerequisites
    satisfied: list[str] = field(default_factory=list)  # hard prerequisites the user already has
    unlocks: int = 0

    @property
    def supplementary(self) -> bool:
        return self.gap is None


# ---------------------------------------------------------------- validation

def _validate(c: RoadmapConstraints) -> None:
    if not (1 <= c.hours_per_week <= 40):
        raise ValueError("hours_per_week must be between 1 and 40")
    if not (1 <= c.duration_weeks <= 26):
        raise ValueError("duration_weeks must be between 1 and 26")


# ---------------------------------------------------------------- step 1: filter

def _actionable_gaps(gaps: list[GapInput]) -> dict[str, GapInput]:
    """Keep real gaps only, one per skill key (the most important wins on alias collisions)."""
    best: dict[str, GapInput] = {}
    for g in gaps:
        if g.classification == MatchClassification.strong or g.priority == PriorityLevel.none:
            continue
        key = skill_key(g.skill_name)
        cur = best.get(key)
        if cur is None or _gap_sort(g) < _gap_sort(cur):
            best[key] = g
    return best


def _gap_sort(g: GapInput) -> tuple:
    return (PRIORITY_RANK[g.priority], IMPORTANCE_RANK[g.importance], CLASSIFICATION_RANK[g.classification])


# ---------------------------------------------------------------- step 2: prerequisites

def _build_nodes(gaps: dict[str, GapInput], known: set[str], c: RoadmapConstraints) -> dict[str, _Node]:
    nodes: dict[str, _Node] = {}
    for key, g in gaps.items():
        nodes[key] = _Node(key=key, name=g.skill_name, gap=g, priority_rank=PRIORITY_RANK[g.priority])

    # Add supplementary nodes for hard prerequisites that are neither known nor in the gap set.
    queue = list(nodes)
    while queue:
        key = queue.pop()
        node = nodes[key]
        for p in hard_prereqs(key):
            if p in nodes:
                continue
            if p in known:
                continue
            nodes[p] = _Node(key=p, name=display_name(p), gap=None, priority_rank=PRIORITY_RANK[PriorityLevel.low])
            queue.append(p)

    # Wire edges (only between skills that are in the plan) and record satisfied prerequisites.
    for key, node in nodes.items():
        for p in hard_prereqs(key):
            if p in nodes:
                node.hard.add(p)
            elif p in known:
                node.satisfied.append(display_name(p))
        for p in soft_prereqs(key):
            if p in nodes and p not in node.hard:
                node.soft.add(p)

    # Size/hours. Supplementary prerequisites are "basics only": always small effort, so a
    # missing foundation never crowds out the skills Module 4 actually flagged.
    for node in nodes.values():
        node.size = EffortSize.small if node.supplementary else base_size(node.key)
        node.hours = estimate_hours(node.size, node.gap.classification if node.gap else None, c.experience_level)
    return nodes


def _propagate_priority(nodes: dict[str, _Node]) -> None:
    """A prerequisite inherits the highest tier of the skills that depend on it (ordering only;
    a gap's displayed priority stays exactly what Module 4 said)."""
    for n in nodes.values():
        n.effective_rank = n.priority_rank
    changed = True
    while changed:
        changed = False
        for n in nodes.values():
            for p in n.hard:
                if n.effective_rank < nodes[p].effective_rank:
                    nodes[p].effective_rank = n.effective_rank
                    changed = True
    for n in nodes.values():
        if n.supplementary:
            n.priority_rank = n.effective_rank


def _count_unlocks(nodes: dict[str, _Node]) -> None:
    children: dict[str, set[str]] = {k: set() for k in nodes}
    for n in nodes.values():
        for p in n.hard | n.soft:
            children[p].add(n.key)

    def descendants(k: str, seen: set[str]) -> set[str]:
        for ch in children[k]:
            if ch not in seen:
                seen.add(ch)
                descendants(ch, seen)
        return seen

    for k, n in nodes.items():
        n.unlocks = len(descendants(k, set()))


# ---------------------------------------------------------------- step 3: ordering

def _sort_key(n: _Node) -> tuple:
    if n.gap:
        imp, cls, sim = IMPORTANCE_RANK[n.gap.importance], CLASSIFICATION_RANK[n.gap.classification], n.gap.similarity_score or 0.0
    else:
        imp, cls, sim = 0, 0, 0.0
    return (n.effective_rank, imp, -n.unlocks, cls, n.hours, sim, n.name.lower(), n.key)


def _order(nodes: dict[str, _Node]) -> list[str]:
    """Kahn's algorithm; among ready skills, the priority sort key decides."""
    indegree = {k: len(n.hard | n.soft) for k, n in nodes.items()}
    children: dict[str, set[str]] = {k: set() for k in nodes}
    for n in nodes.values():
        for p in n.hard | n.soft:
            children[p].add(n.key)

    heap = [(_sort_key(nodes[k]), k) for k, d in indegree.items() if d == 0]
    heapq.heapify(heap)
    order: list[str] = []
    while heap:
        _, k = heapq.heappop(heap)
        order.append(k)
        for ch in children[k]:
            indegree[ch] -= 1
            if indegree[ch] == 0:
                heapq.heappush(heap, (_sort_key(nodes[ch]), ch))
    if len(order) != len(nodes):
        raise ValueError("Dependency cycle detected in roadmap skills")
    return order


# ---------------------------------------------------------------- step 4: time fit

def _hard_closure(key: str, nodes: dict[str, _Node]) -> set[str]:
    out: set[str] = set()
    stack = list(nodes[key].hard)
    while stack:
        k = stack.pop()
        if k not in out:
            out.add(k)
            stack.extend(nodes[k].hard)
    return out


def _fit(order: list[str], nodes: dict[str, _Node], allowed_hours: float):
    """Greedy pass in dependency order.

    Supplementary prerequisites are scheduled only as part of a dependent that fits, so time is
    never spent on a prerequisite whose dependents were all deferred. Later, smaller independent
    items may still backfill leftover capacity because a deferral does not stop the scan.
    """
    scheduled: dict[str, tuple[float, bool]] = {}   # key -> (hours, reduced_scope)
    deferred: dict[str, str] = {}                   # key -> reason
    used = 0.0

    for key in order:
        n = nodes[key]
        if n.supplementary:
            continue
        closure = _hard_closure(key, nodes)

        blocked = [c for c in closure if not nodes[c].supplementary and c not in scheduled]
        if blocked:
            names = ", ".join(sorted(nodes[c].name for c in blocked))
            deferred[key] = f"Depends on {names}, which could not be scheduled in the available time."
            continue

        need_supp = [c for c in closure if nodes[c].supplementary and c not in scheduled]
        supp_hours = sum(nodes[c].hours for c in need_supp)

        chosen: tuple[float, bool] | None = None
        if used + supp_hours + n.hours <= allowed_hours:
            chosen = (n.hours, False)
        elif n.gap and n.gap.priority == PriorityLevel.high:
            r = reduced_hours(n.hours)
            if r < n.hours and used + supp_hours + r <= allowed_hours:
                chosen = (r, True)

        if chosen is None:
            deferred[key] = "Did not fit within the available time."
            continue

        for c in need_supp:
            scheduled[c] = (nodes[c].hours, False)
            used += nodes[c].hours
        scheduled[key] = chosen
        used += chosen[0]

    return scheduled, deferred


# ---------------------------------------------------------------- step 5: weeks

def _weeks(start_hour: float, hours: float, hpw: int, total_weeks: int) -> tuple[int, int]:
    eps = 1e-9
    start = int(math.floor(start_hour / hpw + eps)) + 1
    end = int(math.ceil((start_hour + hours) / hpw - eps))
    start = min(max(start, 1), total_weeks)
    end = min(max(end, start), total_weeks)
    return start, end


# ---------------------------------------------------------------- reasons

def _join(names: list[str], limit: int = 3) -> str:
    names = names[:limit] if len(names) > limit else names
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def _reason(n: _Node, dependents: list[str], reduced: bool) -> str:
    if n.supplementary:
        text = f"A prerequisite for {_join(dependents)} that is not yet in your profile."
    else:
        g = n.gap
        who = {Importance.required: "Required", Importance.preferred: "Preferred", Importance.optional: "Listed as optional"}[g.importance]
        if g.classification == MatchClassification.gap:
            text = f"{who} by the target role and not currently demonstrated in your profile."
        elif g.classification == MatchClassification.transferable:
            rel = f" ({g.matched_skill_name})" if g.matched_skill_name else ""
            text = f"{who} by the target role. Your profile shows related skills{rel} that transfer, but not this skill directly."
        else:
            rel = f" through {g.matched_skill_name}" if g.matched_skill_name else ""
            text = f"{who} by the target role. Your profile partially covers it{rel}; this closes the remaining gap."
        if dependents:
            text += f" Also a prerequisite for {_join(dependents)}."
    if reduced:
        text += " Scoped to core topics because time is limited."
    return text


# ---------------------------------------------------------------- public API

def plan_roadmap(plan_input: PlanInput, constraints: RoadmapConstraints) -> RulePlan:
    _validate(constraints)
    capacity = float(constraints.hours_per_week * constraints.duration_weeks)
    allowed = capacity * (1 + CAPACITY_TOLERANCE)
    known = {skill_key(s) for s in plan_input.known_skills}

    gaps = _actionable_gaps(plan_input.gaps)
    already_known = sorted(set(plan_input.known_skills))

    if not gaps:
        return RulePlan(
            target_role=plan_input.target_role,
            capacity_hours=capacity,
            scheduled_hours=0.0,
            items=[],
            already_known=already_known,
            feasibility_note=NOTE_NO_GAPS,
            has_gaps=False,
        )

    nodes = _build_nodes(gaps, known, constraints)
    _propagate_priority(nodes)
    _count_unlocks(nodes)
    order = _order(nodes)
    scheduled, deferred = _fit(order, nodes, allowed)

    included = [k for k in order if k in scheduled or k in deferred]
    included_set = set(included)

    dependents: dict[str, list[str]] = {k: [] for k in included}
    for k in included:
        for p in nodes[k].hard:
            if p in included_set:
                dependents[p].append(nodes[k].name)

    items: list[PlannedItem] = []
    cursor = 0.0
    for idx, k in enumerate(included):
        n = nodes[k]
        is_sched = k in scheduled
        hours, reduced = scheduled[k] if is_sched else (n.hours, False)
        start = end = None
        if is_sched:
            start, end = _weeks(cursor, hours, constraints.hours_per_week, constraints.duration_weeks)
            cursor += hours
        prereqs = [nodes[p].name for p in sorted(n.hard | n.soft, key=order.index) if p in included_set]
        items.append(PlannedItem(
            skill_key=k,
            skill_name=n.name,
            job_requirement_id=n.gap.job_requirement_id if n.gap else None,
            gap_classification=n.gap.classification if n.gap else None,
            importance=n.gap.importance if n.gap else None,
            priority=n.gap.priority if n.gap else _RANK_TO_PRIORITY[n.priority_rank],
            effort_size=n.size,
            estimated_hours=hours,
            is_scheduled=is_sched,
            start_week=start,
            end_week=end,
            order_index=idx,
            prerequisites=prereqs,
            satisfied_prerequisites=sorted(n.satisfied),
            prerequisite_for=dependents[k],
            is_supplementary=n.supplementary,
            reduced_scope=reduced,
            reason=_reason(n, dependents[k], reduced),
            deferred_reason=None if is_sched else deferred[k],
        ))

    scheduled_hours = float(sum(i.estimated_hours for i in items if i.is_scheduled))
    any_deferred = any(not i.is_scheduled for i in items)
    any_reduced = any(i.reduced_scope for i in items)
    if any_deferred or any_reduced:
        note = NOTE_TIME_INSUFFICIENT
    elif scheduled_hours > TIGHT_PLAN_UTILISATION * capacity:
        note = NOTE_TIGHT_PLAN.format(pct=round(scheduled_hours / capacity * 100))
    else:
        note = None

    return RulePlan(
        target_role=plan_input.target_role,
        capacity_hours=capacity,
        scheduled_hours=scheduled_hours,
        items=items,
        already_known=already_known,
        feasibility_note=note,
        has_gaps=True,
    )