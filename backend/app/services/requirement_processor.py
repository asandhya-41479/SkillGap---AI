import re

from app.models.job import Importance, RequirementCategory
from app.services.skill_normalization import normalize_skill_name

VALID_CATEGORIES = {c.value for c in RequirementCategory}
VALID_IMPORTANCE = {i.value for i in Importance}
MAX_ALTERNATIVES = 5


def _clean_alternatives(raw, name: str, source_text: str | None) -> list[str]:
    """Keep only alternatives that are real strings and are actually written in the job text.

    This is the anti-invention guard: Gemini may group options, but it cannot add an option
    the employer never wrote. Without the job text nothing can be checked, so nothing is kept.
    """
    if not source_text or not isinstance(raw, list):
        return []
    text = source_text.lower()
    out: list[str] = []
    for alt in raw:
        if not isinstance(alt, str) or not alt.strip():
            continue
        if alt.strip().lower() not in text:
            continue
        norm = normalize_skill_name(alt)
        if norm.lower() == name.lower() or norm.lower() in (a.lower() for a in out):
            continue
        out.append(norm)
        if len(out) == MAX_ALTERNATIVES:
            break
    return out


def process_extraction(raw_items: list[dict], source_text: str | None = None) -> list[dict]:
    """Validate, normalize, and deduplicate Gemini's raw extraction output.
    Malformed individual entries are dropped rather than failing the whole batch.

    source_text is the job description; it is used to verify alternatives (see _clean_alternatives).
    """
    seen: dict[str, dict] = {}

    for item in raw_items:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        normalized_name = normalize_skill_name(name)

        category = item.get("category")
        if category not in VALID_CATEGORIES:
            category = RequirementCategory.other.value

        importance = item.get("importance")
        if importance not in VALID_IMPORTANCE:
            importance = Importance.optional.value

        alternatives = _clean_alternatives(item.get("alternatives"), normalized_name, source_text)

        # Deduplicate by normalized name; keep the more important of the two if seen twice,
        # and keep every verified alternative from both.
        existing = seen.get(normalized_name)
        if existing is None:
            seen[normalized_name] = {"skill_name": normalized_name, "category": category,
                                     "importance": importance, "alternatives": alternatives}
            continue
        if _importance_rank(importance) > _importance_rank(existing["importance"]):
            existing["category"], existing["importance"] = category, importance
        for alt in alternatives:
            if alt.lower() not in (a.lower() for a in existing["alternatives"]) and len(existing["alternatives"]) < MAX_ALTERNATIVES:
                existing["alternatives"].append(alt)

    if source_text:
        _group_from_text(seen, source_text)
    return _fold_listed_alternatives(seen)


# "Vector Databases (Pinecone, FAISS or Chroma)"  -> head + a parenthesised list containing "or"
_PAREN_LIST = re.compile(r"([^,:;()\n]+?)\s*\(([^()]*\bor\b[^()]*)\)", re.IGNORECASE)
# splits a parenthesised list: "Pinecone, FAISS or Chroma" -> Pinecone | FAISS | Chroma
_SPLIT_LIST = re.compile(r",|\bor\b|\band/or\b", re.IGNORECASE)


def _lookup(seen: dict[str, dict], phrase: str) -> dict | None:
    phrase = phrase.strip(" -*\u2022\t.").strip()
    if not phrase:
        return None
    norm = normalize_skill_name(phrase).lower()
    for item in seen.values():
        if item["skill_name"].lower() == norm:
            return item
    return None


def _merge(head: dict, members: list[dict]) -> None:
    for m in members:
        if m is head:
            continue
        if m["skill_name"].lower() not in (a.lower() for a in head["alternatives"]) \
                and len(head["alternatives"]) < MAX_ALTERNATIVES:
            head["alternatives"].append(m["skill_name"])
        if _importance_rank(m["importance"]) > _importance_rank(head["importance"]):
            head["importance"] = m["importance"]


def _group_from_text(seen: dict[str, dict], source_text: str) -> None:
    """Deterministic backstop for alternatives: read "X, Y or Z" straight from the job text.

    Gemini is asked to group alternatives, but does not always do it. This finds them in the
    text itself and only groups requirements that were already extracted, so it can never add
    a skill. "/" is deliberately NOT treated as "or" ("HTML/CSS" usually means both).
    """
    used: set[int] = set()
    for head_text, inner in _PAREN_LIST.findall(source_text):
        members = [m for m in (_lookup(seen, t) for t in _SPLIT_LIST.split(inner)) if m]
        unique = list({id(m): m for m in members}.values())
        if len(unique) < 1:
            continue
        head = _lookup(seen, head_text.split("\n")[-1])
        if head is None:
            if len(unique) < 2:
                continue
            head = unique[0]
        _merge(head, unique)
        used.update(id(m) for m in unique)
        used.add(id(head))

    text_wo_parens = _PAREN_LIST.sub(" ", source_text)
    # Outside parentheses only the two sides of "or" are grouped: "AWS or GCP". A longer comma list
    # ("Python, SQL, Docker or Kubernetes") is ambiguous, and grouping required skills by mistake
    # would hide real gaps, so it is left as separate requirements (safe side).
    for piece in re.split(r"[;:\n]|\.\s", text_wo_parens):
        for chunk in piece.split(","):
            if not re.search(r"\bor\b", chunk, re.IGNORECASE):
                continue
            run = [_lookup(seen, t) for t in re.split(r"\bor\b|\band/or\b", chunk, flags=re.IGNORECASE)]
            if any(m is None for m in run):
                continue
            unique = [m for m in {id(m): m for m in run}.values() if id(m) not in used]
            if len(unique) >= 2:
                _merge(unique[0], unique)
                used.update(id(m) for m in unique)


def _fold_listed_alternatives(seen: dict[str, dict]) -> list[dict]:
    """If an option was ALSO returned as its own item, drop that duplicate item.

    "Vector Databases (Pinecone, FAISS or Chroma)" must be one requirement, not four. The group
    keeps the higher importance of the two, so nothing the employer asked for gets weaker.
    """
    in_group: dict[str, dict] = {}
    for item in seen.values():
        for alt in item["alternatives"]:
            in_group.setdefault(alt.lower(), item)

    result = []
    for item in seen.values():
        group = in_group.get(item["skill_name"].lower())
        if group is not None and group is not item:
            if _importance_rank(item["importance"]) > _importance_rank(group["importance"]):
                group["importance"] = item["importance"]
            continue
        result.append(item)
    return result


def _importance_rank(importance: str) -> int:
    return {"required": 2, "preferred": 1, "optional": 0}.get(importance, 0)
