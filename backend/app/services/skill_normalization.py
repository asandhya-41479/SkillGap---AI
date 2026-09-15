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
    "python 3": "Python",
    "python3": "Python",
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
    "restful api": "REST API",
    "restful apis": "REST API",
    "rest apis": "REST API",
    "rest api": "REST API",
    "rest": "REST API",

    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "rag pipelines": "RAG",
    "rag pipeline": "RAG",
    "llm": "LLM",
    "llms": "LLM",
    "large language models": "LLM",
    "git": "Git",
    "vue": "Vue",
    "vue.js": "Vue",
    "vuejs": "Vue",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "c++": "C++",
    "c#": "C#",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
}


def normalize_skill_name(raw_name: str) -> str:
    """Collapse known aliases to a canonical name. Unknown skills pass through
    with whitespace trimmed/collapsed but original casing preserved, since we
    can't safely guess correct casing for arbitrary tech names (e.g. FastAPI)."""
    cleaned = " ".join(raw_name.strip().split())
    key = cleaned.lower()
    return ALIASES.get(key, cleaned)