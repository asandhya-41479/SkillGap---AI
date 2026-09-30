"""Skill-key normalization and static prerequisite lookups."""
from app.core.roadmap_config import DEPENDENCIES, DISPLAY_NAMES, EXTRA_ALIASES
from app.services.skill_normalization import normalize_skill_name


def skill_key(name: str) -> str:
    """Canonical lowercase key: Module 2 normalization, then the small extra alias table."""
    key = normalize_skill_name(name).lower()
    return EXTRA_ALIASES.get(key, key)


def display_name(key: str) -> str:
    return DISPLAY_NAMES.get(key, key.title())


def hard_prereqs(key: str) -> list[str]:
    return list(DEPENDENCIES.get(key, {}).get("hard", []))


def soft_prereqs(key: str) -> list[str]:
    return list(DEPENDENCIES.get(key, {}).get("soft", []))


def find_cycle() -> list[str] | None:
    """Return a cycle in the static graph (hard + soft edges), or None. Used by tests as a guard."""
    state: dict[str, int] = {}  # 1 = visiting, 2 = done

    def visit(k: str, path: list[str]) -> list[str] | None:
        if state.get(k) == 2:
            return None
        if state.get(k) == 1:
            return path[path.index(k):] + [k]

        state[k] = 1
        for p in hard_prereqs(k) + soft_prereqs(k):
            cycle = visit(p, path + [k])
            if cycle:
                return cycle
        state[k] = 2
        return None

    for k in list(DEPENDENCIES):
        cycle = visit(k, [])
        if cycle:
            return cycle
    return None