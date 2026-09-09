ALIASES: dict[str, str] = {
    "react.js": "React",
    "reactjs": "React",
    "react": "React",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "py": "Python",
    "python": "Python",
    "fastapi": "FastAPI",
    "docker": "Docker",
    "aws": "AWS",
    "amazon web services": "AWS",
    "gcp": "Google Cloud Platform",
    "google cloud": "Google Cloud Platform",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "html/css": "HTML",
}


def normalize_skill_name(raw_name: str) -> str:
    """Collapse known aliases to a canonical name. Unknown skills pass through
    with whitespace trimmed/collapsed but original casing preserved, since we
    can't safely guess correct casing for arbitrary tech names (e.g. FastAPI)."""
    cleaned = " ".join(raw_name.strip().split())
    key = cleaned.lower()
    return ALIASES.get(key, cleaned)