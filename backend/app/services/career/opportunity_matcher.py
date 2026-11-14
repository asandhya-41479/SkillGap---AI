"""Module 7 Step 7: opportunity matching. Pure and deterministic; Gemini is never used and never sees job text.

Pasted job description -> requirements:
  1. Vocabulary = the user's own skills + their saved Module 3 requirements + the Module 3 alias table +
     a curated list of common skills. Only these names can be found: nothing is invented.
  2. Whole-word scan of the text (longest names first, ambiguous short words like "rest" or "go" skipped).
  3. Importance from the text's own structure: lines under a "Requirements / Must have" heading -> required,
     under "Nice to have / Preferred / Bonus" -> preferred; a line saying "preferred"/"a plus" marks its skills
     preferred. If the text has no such signals, every skill is weighted equally (flagged in the result).
Score = Module 4's own alignment formula: sum(importance weight x match credit) / sum(weights) x 100,
with the SAME weights (required 2, preferred 1, optional 0.5) and credits (strong 1, partial 0.5,
transferable 0.25, gap 0). It is a requirement-coverage number, never a hiring probability.
"""
import hashlib
import re

# Module 4 values (app/core/skill_gap_config.py IMPORTANCE_WEIGHT / CLASSIFICATION_CREDIT); a DB test keeps them in sync
IMPORTANCE_WEIGHT = {"required": 2.0, "preferred": 1.0, "optional": 0.5}
CLASSIFICATION_CREDIT = {"strong": 1.0, "partial": 0.5, "transferable": 0.25, "gap": 0.0}

MAX_REQUIREMENTS = 40

# words that are skills only in some contexts: never matched from free text
AMBIGUOUS = {"rest", "go", "r", "c", "js", "ts", "py", "node", "ml", "ai", "sense", "flow", "agile"}
# skill names that are also ordinary English words: matched only when written with a capital letter
# ("React" yes, "react quickly" no)
CASE_SENSITIVE = {"react", "rust", "spring", "express", "swift", "excel", "shell", "flask", "angular", "dart"}

# curated common skills with their Module 3 RequirementCategory (category feeds Module 4 matching)
COMMON_SKILLS = {
    "Python": "programming_language", "Java": "programming_language", "JavaScript": "programming_language",
    "TypeScript": "programming_language", "C++": "programming_language", "C#": "programming_language",
    "Rust": "programming_language", "Kotlin": "programming_language", "PHP": "programming_language",
    "HTML": "programming_language", "CSS": "programming_language", "Golang": "programming_language",
    "React": "framework", "Vue": "framework", "Angular": "framework", "Next.js": "framework",
    "Node.js": "framework", "Django": "framework", "Flask": "framework", "FastAPI": "framework",
    "Spring Boot": "framework", "Express.js": "framework", "Tailwind CSS": "framework",
    "Pandas": "library", "NumPy": "library", "scikit-learn": "library", "TensorFlow": "library",
    "PyTorch": "library", "LangChain": "library", "Redux": "library", "SQLAlchemy": "library",
    "SQL": "database", "PostgreSQL": "database", "MySQL": "database", "MongoDB": "database", "Redis": "database",
    "SQLite": "database",
    "Docker": "devops", "Kubernetes": "devops", "CI/CD": "devops", "GitHub Actions": "devops",
    "Jenkins": "devops", "Terraform": "devops", "Linux": "devops",
    "AWS": "cloud", "Azure": "cloud", "Google Cloud Platform": "cloud",
    "REST API": "api", "GraphQL": "api", "JWT": "api", "OAuth": "api",
    "Git": "tool", "Pytest": "tool", "Selenium": "tool", "Tableau": "tool", "Power BI": "tool", "Jira": "tool",
    "Machine Learning": "ai_ml", "Deep Learning": "ai_ml", "NLP": "ai_ml", "LLM": "ai_ml", "RAG": "ai_ml",
    "Prompt Engineering": "ai_ml", "Embeddings": "ai_ml", "Computer Vision": "ai_ml", "Vector Databases": "ai_ml",
    "Data Structures": "concept", "Algorithms": "concept", "System Design": "concept", "OOP": "concept",
    "Microservices": "concept", "Data Analysis": "concept",
}

_PREFERRED = re.compile(r"\b(nice[- ]to[- ]have|good[- ]to[- ]have|preferred|bonus|a plus|desirable|optional)\b", re.I)
_REQUIRED = re.compile(r"\b(requirements?|required|must[- ]have|must|qualifications|what you need|you have)\b", re.I)


def text_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.lower().split()).encode()).hexdigest()


def build_vocabulary(user_skills: list[tuple[str, str]], saved_requirements: list[tuple[str, str]],
                     aliases: dict[str, str]) -> dict[str, tuple[str, str]]:
    """term (lower) -> (canonical name, category). Earlier sources win, so the user's own spelling is kept."""
    vocab: dict[str, tuple[str, str]] = {}
    known_cat = {n.lower(): c for n, c in list(COMMON_SKILLS.items()) + saved_requirements + user_skills}

    def add(term: str, name: str, cat: str):
        t = " ".join(term.lower().split())
        if t and t not in AMBIGUOUS and t not in vocab:
            vocab[t] = (name, cat or known_cat.get(name.lower(), "other"))

    for name, cat in user_skills:
        add(name, name, cat)
    for name, cat in saved_requirements:
        add(name, name, cat)
    for name, cat in COMMON_SKILLS.items():
        add(name, name, cat)
    for alias, canonical in aliases.items():
        add(alias, canonical, known_cat.get(canonical.lower(), "other"))
        add(canonical, canonical, known_cat.get(canonical.lower(), "other"))
    return vocab


def _pattern(term: str) -> re.Pattern:
    """Whole-word match that works for C++, C#, Node.js, CI/CD; allows a plural "s" ("REST APIs") and a
    sentence-ending ".". English-word skills (CASE_SENSITIVE) must start with a capital letter."""
    body = re.escape(term)
    if term in CASE_SENSITIVE:
        body = f"(?-i:{re.escape(term[0].upper())})(?i:{re.escape(term[1:])})"
    return re.compile(rf"(?<![a-z0-9+#./-]){body}s?(?![a-z0-9+#]|\.[a-z0-9])", re.I)


def extract_requirements(text: str, vocab: dict[str, tuple[str, str]]) -> tuple[list[dict], bool]:
    """Returns ([{name, category, importance}], importance_detected)."""
    terms = sorted(vocab, key=len, reverse=True)
    patterns = {t: _pattern(t) for t in terms}
    section = None                     # None | "required" | "preferred"
    found: dict[str, dict] = {}
    detected = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        is_heading = len(line) <= 60 and (line.endswith(":") or line.isupper() or line.startswith("#"))
        if is_heading and _PREFERRED.search(line):
            section, detected = "preferred", True
            continue
        if is_heading and _REQUIRED.search(line):
            section, detected = "required", True
            continue
        line_imp = section
        if _PREFERRED.search(line):
            line_imp, detected = "preferred", True
        elif _REQUIRED.search(line) and section is None:
            line_imp, detected = "required", True
        masked = line
        for t in terms:                # longest first; mask matches so "Node.js" does not also match "js"
            if patterns[t].search(masked):
                name, cat = vocab[t]
                imp = line_imp or "required"
                cur = found.get(name.lower())
                if cur is None:
                    found[name.lower()] = dict(name=name, category=cat, importance=imp)
                elif cur["importance"] == "preferred" and imp == "required":
                    cur["importance"] = "required"     # required anywhere wins
                masked = patterns[t].sub(" ", masked)
    reqs = list(found.values())[:MAX_REQUIREMENTS]
    return reqs, detected


def score(requirements: list[dict], classifications: dict[str, str], equal_weights: bool) -> tuple[float, dict]:
    """Module 4 alignment formula over the given requirements. classifications: name.lower() -> class."""
    total = credit = 0.0
    bd = dict(strong=[], partial=[], transferable=[], missing=[], critical=[])
    for r in requirements:
        cls = classifications.get(r["name"].lower(), "gap")
        w = 1.0 if equal_weights else IMPORTANCE_WEIGHT[r["importance"]]
        total += w
        credit += w * CLASSIFICATION_CREDIT[cls]
        bd["missing" if cls == "gap" else cls].append(r["name"])
        if cls == "gap" and r["importance"] == "required":
            bd["critical"].append(r["name"])
    return (round(100 * credit / total, 1) if total else 0.0), bd


def summary(pct: float, source: str) -> str:
    where = "this saved job" if source == "SAVED_JOB" else "the requirements found in this description"
    # round half up, like the frontend's Math.round (Python's format would turn 62.5 into "62")
    return f"Your profile matches approximately {int(pct + 0.5)}% of {where}."
