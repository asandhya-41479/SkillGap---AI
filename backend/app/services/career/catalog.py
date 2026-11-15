"""Module 7: curated, deterministic action catalog.

Every action title comes from a template here. A skill without a specific entry uses its Module 3 category's
evidence type. Gemini never adds or chooses actions; it may only reword the explanation later (Step 4).
"""

# evidence_type decides which action follows "knows it but cannot prove it":
#   codebase        -> BUILD/PROVE in a repository
#   deployable      -> PROVE with a deployment (Dockerfile, config, live URL)
#   ai_pipeline     -> BUILD a working pipeline with a demo
#   problem_solving -> PRACTICE (evidence is solved problems, not a project)
#   conceptual      -> PREPARE (explain it in interviews / a design write-up)
CATEGORY_EVIDENCE_TYPE = {
    "programming_language": "codebase",
    "framework": "codebase",
    "library": "codebase",
    "database": "codebase",
    "api": "codebase",
    "tool": "codebase",
    "ai_ml": "ai_pipeline",
    "cloud": "deployable",
    "devops": "deployable",
    "concept": "conceptual",
    "other": "codebase",
}

# Skill-specific overrides (keys are skill_key() form: normalized + lower-case)
SKILL_EVIDENCE_TYPE = {
    "docker": "deployable", "kubernetes": "deployable", "aws": "deployable", "azure": "deployable",
    "google cloud platform": "deployable", "terraform": "deployable", "ci/cd": "deployable",
    "github actions": "deployable", "linux": "deployable",
    "rag": "ai_pipeline", "llm": "ai_pipeline", "machine learning": "ai_pipeline", "deep learning": "ai_pipeline",
    "nlp": "ai_pipeline", "langchain": "ai_pipeline", "vector databases": "ai_pipeline", "faiss": "ai_pipeline",
    "embeddings": "ai_pipeline", "prompt engineering": "ai_pipeline",
    "dsa": "problem_solving", "data structures": "problem_solving", "algorithms": "problem_solving",
    "data structures and algorithms": "problem_solving", "problem solving": "problem_solving",
    "git": "repository_practice", "github": "repository_practice", "version control": "repository_practice",
    "browser debugging tools": "debugging", "chrome devtools": "debugging", "devtools": "debugging",
    "debugging": "debugging",
    "responsive design": "frontend_ui", "css flexbox": "frontend_ui", "css grid": "frontend_ui",
    "web accessibility (wcag)": "frontend_ui", "web accessibility": "frontend_ui", "accessibility": "frontend_ui",
    "system design": "conceptual", "oop": "conceptual", "object-oriented programming": "conceptual",
    "design patterns": "conceptual", "agile": "conceptual", "microservices": "conceptual",
}

EVIDENCE_REQUIRED = {
    "codebase": ["A GitHub repository where {skill} is used in real code", "README explaining how {skill} is used"],
    "deployable": ["{skill} configuration committed to a GitHub repository", "Deployment URL or documented deployment steps"],
    "ai_pipeline": ["GitHub repository with a working {skill} pipeline", "README with an architecture diagram",
                    "Working demo or recorded walkthrough"],
    "problem_solving": ["A log or repository of solved {skill} problems with your solutions"],
    "conceptual": ["A short design write-up or notes explaining {skill} with an example from your work"],
    # any repository shows version-control practice, so these skills are always PROVE, never "build a project"
    "repository_practice": ["A public GitHub repository with a meaningful commit history",
                            "A README, and branches or pull requests used in your workflow"],
    # a tool used while coding: proof is a real bug you investigated, not a repository "using" the tool
    "debugging": ["A short write-up of a real bug you found and fixed using {skill} (steps and screenshots)"],
    # visible in a user interface: proof is a page you built
    "frontend_ui": ["A live page or GitHub repository of your own UI that demonstrates {skill}",
                    "Screenshots (e.g. mobile and desktop) or a note pointing to where {skill} is applied"],
}

# Learning-order fallback used ONLY when a skill has no Module 5 roadmap item (no roadmap yet).
# When a roadmap exists, its own prerequisite graph is used instead. Keys and values: skill_key() form.
KNOWN_PREREQUISITES = {
    "axios": ["rest api", "javascript"], "fetch api": ["rest api", "javascript"],
    "react": ["javascript"], "next.js": ["react"], "redux": ["react"], "state management": ["react"],
    "react testing library": ["react", "jest"], "jest": ["javascript"], "unit testing": ["javascript"],
    "typescript": ["javascript"], "node.js": ["javascript"], "express": ["node.js"],
    "tailwind css": ["css"], "css flexbox": ["css"], "css grid": ["css"], "responsive design": ["css"],
    "fastapi": ["python"], "django": ["python"], "flask": ["python"], "pandas": ["python"],
    "rag": ["embeddings", "llm"], "embeddings": ["python"], "langchain": ["llm", "python"],
    "kubernetes": ["docker"], "ci/cd": ["git"], "github": ["git"], "github actions": ["git"],
    "postgresql": ["sql"], "mysql": ["sql"], "sqlalchemy": ["sql", "python"],
}

# Templates: (category, evidence_type) -> title. {skill} and {project} are filled in.
TITLE_TEMPLATES = {
    ("LEARN", "default"): "Learn {skill} fundamentals",
    ("LEARN", "roadmap"): "Complete your {skill} roadmap milestone",
    ("PRACTICE", "default"): "Practise {skill} with hands-on exercises",
    ("PRACTICE", "roadmap"): "Finish the practical task for {skill} in your roadmap",
    ("PRACTICE", "problem_solving"): "Solve targeted {skill} problems for technical interviews",
    ("BUILD", "codebase"): "Build a small project that uses {skill} end to end",
    ("BUILD", "ai_pipeline"): "Build a working {skill} proof-of-concept with a demo",
    ("BUILD", "deployable"): "Deploy a project using {skill} and document the steps",
    ("PROVE", "codebase"): "Add {skill} to one of your GitHub projects and attach it as evidence",
    ("PROVE", "deployable"): "Add {skill} to one of your GitHub projects (e.g. SkillGap AI) and attach the repo",
    ("PROVE", "ai_pipeline"): "Attach a repository that demonstrates your {skill} work",
    ("PROVE", "roadmap_done"): "You finished the {skill} roadmap item: attach project evidence for it",
    ("BUILD", "frontend_ui"): "Build and publish a page that demonstrates {skill}",
    ("PROVE", "repository_practice"): "Publish one of your projects on GitHub with a clean history and README",
    ("PREPARE", "default"): "Prepare to explain your {skill} work in interviews",
    ("PREPARE", "conceptual"): "Prepare {skill} interview topics with examples from your projects",
}

# Skill-specific titles where a generic template would be vague
SKILL_TITLES = {
    ("docker", "PROVE"): "Dockerize one of your projects (e.g. SkillGap AI backend) and attach the repo",
    ("docker", "BUILD"): "Containerize a project with Docker and document how to run it",
    ("fastapi", "BUILD"): "Build a production-style FastAPI service (auth, validation, tests)",
    ("rag", "BUILD"): "Build a RAG proof-of-concept: embeddings, retrieval and grounded answers",
    ("sql", "PROVE"): "Add SQL schema/migration files to a project and attach the repo",
    ("aws", "LEARN"): "Learn AWS fundamentals (compute, storage, IAM, deployment)",
    ("git", "PROVE"): "Keep a public repository with a clean commit history and README",
    ("github", "LEARN"): "Learn the GitHub workflow (repositories, branches, pull requests)",
    ("browser debugging tools", "LEARN"): "Learn browser DevTools (Elements, Console, Network, debugger)",
}

# APPLY checklist (job-search readiness). Never names companies, openings, salaries or recruiters.
APPLY_CHECKLIST = [
    ("portfolio", "Pin your strongest repositories for {role} on your GitHub profile",
     ["2-3 pinned repositories that use the role's required skills"]),
    ("stories", "Write 3 STAR stories from your projects for {role} interviews",
     ["3 written STAR stories (situation, task, action, result)"]),
    ("readme", "Add README, architecture diagram and demo link to each pinned project",
     ["README with setup steps", "Architecture diagram", "Demo link or screenshots"]),
    ("shortlist", "Compare real {role} job descriptions you find against your profile",
     ["Saved job descriptions compared in Opportunity Matching"]),
]


def evidence_type(skill_key: str, category: str) -> str:
    return SKILL_EVIDENCE_TYPE.get(skill_key) or CATEGORY_EVIDENCE_TYPE.get(category, "codebase")


def title_for(skill: str, skill_key: str, category: str, variant: str) -> str:
    t = SKILL_TITLES.get((skill_key, category))
    if t is None:
        t = TITLE_TEMPLATES.get((category, variant)) or TITLE_TEMPLATES[(category, "default" if (category, "default") in TITLE_TEMPLATES else "codebase")]
    return t.format(skill=skill)


def evidence_required(skill: str, ev_type: str) -> list[str]:
    return [s.format(skill=skill) for s in EVIDENCE_REQUIRED[ev_type]]


# ---------------------------------------------------------------- Step 5: project blueprints
# A small curated set. A blueprint is recommended ONLY when it proves at least one skill that needs a NEW
# project (a BUILD action). Skills that can be proven in an existing repo get PROVE actions instead.
# Keys are skill_key() form (normalized, lower-case).
PROJECT_BLUEPRINTS = [
    dict(id="knowledge-assistant", name="Enterprise Knowledge Assistant (RAG)",
         purpose="Answer questions over your own documents with retrieval-augmented generation.",
         skills={"rag", "embeddings", "vector databases", "faiss", "llm", "prompt engineering", "langchain",
                 "nlp", "fastapi", "python"},
         artifacts=["GitHub repository", "README with an architecture diagram (ingest -> embed -> retrieve -> generate)",
                    "Working demo or recorded walkthrough", "Short note on how answers are grounded and evaluated"]),
    dict(id="ml-prediction-service", name="ML Prediction Service",
         purpose="Train a model on a public dataset and serve predictions through an API.",
         skills={"machine learning", "scikit-learn", "pandas", "numpy", "data analysis", "fastapi", "flask", "python"},
         artifacts=["GitHub repository", "Notebook with data preparation and evaluation metrics",
                    "Prediction API endpoint", "README explaining the model choice"]),
    dict(id="deep-learning-classifier", name="Deep Learning Image Classifier",
         purpose="Train and evaluate a neural network for an image or text classification task.",
         skills={"deep learning", "pytorch", "tensorflow", "keras", "computer vision", "nlp", "python"},
         artifacts=["GitHub repository", "Training and evaluation results", "README with model architecture",
                    "Demo or inference script"]),
    dict(id="fullstack-app", name="Full-Stack Task Manager",
         purpose="A web app with authentication, a REST API and a database.",
         skills={"react", "javascript", "typescript", "html", "css", "node.js", "express", "rest api",
                 "postgresql", "sql", "mongodb", "next.js", "vue"},
         artifacts=["GitHub repository", "Deployed frontend URL", "API documentation", "README with setup steps"]),
    dict(id="production-api", name="Production-Style Backend API",
         purpose="A secured REST API with validation, persistence, tests and background jobs.",
         skills={"fastapi", "django", "flask", "rest api", "postgresql", "sql", "sqlalchemy", "pytest", "redis",
                 "celery", "python", "jwt"},
         artifacts=["GitHub repository", "OpenAPI/Swagger docs", "Automated tests", "README with design decisions"]),
    dict(id="cloud-deployment", name="Cloud Deployment Pipeline",
         purpose="Containerize an existing project and deploy it with an automated pipeline.",
         skills={"aws", "azure", "google cloud platform", "docker", "kubernetes", "ci/cd", "github actions",
                 "terraform", "linux"},
         artifacts=["Infrastructure/config files in the repository", "Live deployment URL",
                    "Pipeline run history", "README with deployment steps"]),
    dict(id="data-dashboard", name="Data Pipeline and Dashboard",
         purpose="Clean a public dataset, store it, and present insights in a dashboard.",
         skills={"pandas", "sql", "data analysis", "data visualization", "power bi", "tableau", "etl",
                 "apache spark", "airflow", "excel", "numpy"},
         artifacts=["GitHub repository", "Dashboard link or screenshots", "Data cleaning notebook",
                    "README with key findings"]),
    dict(id="realtime-chat", name="Real-Time Chat Application",
         purpose="A chat app with live updates over WebSockets.",
         skills={"websockets", "socket.io", "node.js", "react", "redis", "javascript"},
         artifacts=["GitHub repository", "Deployed demo URL", "README explaining the real-time design"]),
    dict(id="microservices-demo", name="Microservices Order System",
         purpose="Two or three small services that communicate through a message broker.",
         skills={"microservices", "kafka", "rabbitmq", "grpc", "docker", "kubernetes"},
         artifacts=["GitHub repository", "Architecture diagram", "docker-compose setup", "README with service contracts"]),
    dict(id="java-spring-api", name="Spring Boot REST API",
         purpose="A layered Java API with persistence and unit tests.",
         skills={"java", "spring boot", "spring", "hibernate", "mysql", "junit", "rest api"},
         artifacts=["GitHub repository", "Unit tests", "API documentation", "README with setup steps"]),
    dict(id="mobile-app", name="Mobile Companion App",
         purpose="A small mobile app that consumes a REST API.",
         skills={"react native", "flutter", "dart", "android", "kotlin", "swift", "ios"},
         artifacts=["GitHub repository", "APK/TestFlight build or screen recording", "README with screenshots"]),
]
MAX_PROJECTS = 3
