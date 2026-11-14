"""Module 7 Step 6: curated interview topic bank (deterministic). Gemini may only phrase questions for these
topics; it never chooses which topics a user prepares. Keys are skill_key() form (normalized, lower-case).
"""

# skill -> focused sub-topics (what interviewers actually probe for this skill)
SKILL_TOPICS = {
    "python": ["data types and mutability", "list/dict comprehensions and generators", "OOP and dunder methods",
               "exceptions and context managers", "async/await basics"],
    "fastapi": ["path operations and dependency injection", "Pydantic validation", "authentication with OAuth2/JWT",
                "async endpoints vs sync", "testing with TestClient"],
    "django": ["ORM and migrations", "views and URL routing", "middleware", "authentication", "DRF serializers"],
    "flask": ["routing and blueprints", "request context", "extensions", "error handling"],
    "sql": ["joins and aggregations", "indexes and query performance", "normalization", "transactions and isolation",
            "window functions"],
    "postgresql": ["indexes (B-tree, partial)", "transactions and locking", "JSON columns", "query plans with EXPLAIN"],
    "docker": ["images vs containers", "Dockerfile layers and caching", "volumes and networking",
               "docker-compose for multi-service apps", "small, secure images"],
    "kubernetes": ["pods, deployments and services", "config maps and secrets", "scaling and health probes"],
    "aws": ["EC2 vs Lambda", "S3 storage", "IAM roles and least privilege", "deploying a web API"],
    "git": ["branching and merging", "rebase vs merge", "resolving conflicts", "pull request workflow"],
    "rest api": ["HTTP methods and status codes", "idempotency", "pagination and filtering", "versioning",
                 "authentication"],
    "javascript": ["closures and scope", "promises and async/await", "event loop", "this binding", "ES modules"],
    "typescript": ["types vs interfaces", "generics", "narrowing", "strict mode"],
    "react": ["components, props and state", "hooks (useState, useEffect)", "rendering and keys", "state management",
              "fetching data from an API"],
    "node.js": ["event loop and non-blocking I/O", "Express middleware", "error handling", "streams"],
    "java": ["OOP principles", "collections", "exceptions", "multithreading basics", "JVM memory"],
    "rag": ["what RAG is and when to use it", "embeddings and chunking strategies", "retrieval vs generation",
            "vector databases", "hallucination control and evaluation"],
    "llm": ["how LLMs generate text", "prompt engineering", "structured output", "hallucinations and grounding",
            "cost and latency trade-offs"],
    "prompt engineering": ["clear instructions and examples", "structured JSON output", "prompt injection",
                           "evaluating prompts"],
    "embeddings": ["what an embedding represents", "cosine similarity", "choosing an embedding model",
                   "semantic search"],
    "vector databases": ["approximate nearest neighbour search", "indexing", "metadata filtering"],
    "machine learning": ["supervised vs unsupervised learning", "overfitting and regularization", "train/test split and cross-validation",
                         "evaluation metrics", "feature engineering"],
    "deep learning": ["neural network basics", "backpropagation", "CNNs vs RNNs vs transformers", "overfitting"],
    "nlp": ["tokenization", "embeddings", "transformers", "text classification"],
    "pandas": ["DataFrame operations", "groupby and aggregation", "merging", "handling missing data"],
    "data analysis": ["exploratory analysis", "summary statistics", "visualization choices", "communicating findings"],
    "ci/cd": ["pipeline stages", "automated tests in CI", "deployment strategies", "secrets in pipelines"],
    "linux": ["file permissions", "processes", "shell basics", "networking commands"],
    "dsa": ["arrays and hashing", "two pointers and sliding window", "trees and graphs", "time and space complexity",
            "recursion and dynamic programming"],
    "system design": ["requirements and scale estimates", "caching", "databases and indexing", "API design",
                      "reliability and failure handling"],
    "oop": ["encapsulation, inheritance, polymorphism", "composition vs inheritance", "SOLID principles"],
}

# fallback sub-topics by Module 3 requirement category, for skills without a curated entry
CATEGORY_TOPICS = {
    "programming_language": ["core syntax and data types", "error handling", "writing clean, testable code"],
    "framework": ["core concepts and project structure", "request/response lifecycle", "testing", "common pitfalls"],
    "library": ["main use cases", "core API", "when not to use it"],
    "database": ["data modelling", "querying", "indexes and performance", "transactions"],
    "ai_ml": ["core concepts", "evaluation", "limitations and risks", "how you applied it in a project"],
    "cloud": ["core services", "security and IAM", "deployment", "cost awareness"],
    "devops": ["core concepts", "automation", "deployment", "troubleshooting"],
    "api": ["design principles", "authentication", "error handling", "documentation"],
    "tool": ["typical workflow", "how you used it in a project", "common problems"],
    "concept": ["definition and trade-offs", "an example from your work", "common interview questions"],
    "other": ["core concepts", "how you used it in a project"],
}

# role fundamentals: matched by WHOLE-WORD keywords in the Module 3 target_role text, specific roles first
# (so "Frontend Developer" is not caught by the generic "developer", and "ai" never matches inside "Retail")
ROLE_FUNDAMENTALS = [
    (("ai", "ml", "machine learning", "data scientist", "data science", "nlp", "llm", "genai"),
     [("role:ml_fundamentals", "ML and LLM fundamentals", ["model evaluation", "overfitting", "LLM limitations"]),
      ("role:dsa", "Data structures and algorithms", ["arrays and hashing", "complexity analysis"]),
      ("role:behavioral", "Behavioural interview (STAR stories)", ["a project you are proud of", "a hard bug you solved"])]),
    (("frontend", "front-end", "ui", "react"),
     [("role:web_fundamentals", "Web fundamentals", ["HTTP", "browser rendering", "accessibility"]),
      ("role:dsa", "Data structures and algorithms", ["arrays and strings", "complexity analysis"]),
      ("role:behavioral", "Behavioural interview (STAR stories)", ["a project you are proud of", "feedback"])]),
    (("data analyst", "analyst", "business intelligence", "bi"),
     [("role:sql_analytics", "SQL for analytics", ["joins", "aggregations", "window functions"]),
      ("role:statistics", "Statistics basics", ["distributions", "hypothesis testing"]),
      ("role:behavioral", "Behavioural interview (STAR stories)", ["presenting insights", "a hard problem"])]),
    (("devops", "cloud", "sre", "site reliability"),
     [("role:system_design", "System design basics", ["reliability", "monitoring", "scaling"]),
      ("role:linux_networking", "Linux and networking", ["processes", "DNS and HTTP"]),
      ("role:behavioral", "Behavioural interview (STAR stories)", ["an incident you handled", "automation"])]),
    (("backend", "api", "python developer", "software engineer", "full stack", "full-stack", "developer"),
     [("role:system_design", "System design basics", ["API design", "caching", "databases and scaling"]),
      ("role:dsa", "Data structures and algorithms", ["arrays and hashing", "complexity analysis"]),
      ("role:behavioral", "Behavioural interview (STAR stories)", ["a project you are proud of", "teamwork"])]),
]
DEFAULT_FUNDAMENTALS = [
    ("role:dsa", "Data structures and algorithms", ["arrays and hashing", "complexity analysis"]),
    ("role:oop", "Object-oriented programming", ["encapsulation", "inheritance vs composition"]),
    ("role:behavioral", "Behavioural interview (STAR stories)", ["a project you are proud of", "a hard bug you solved"]),
]


def topics_for(skill_key: str, category: str) -> list[str]:
    return SKILL_TOPICS.get(skill_key) or CATEGORY_TOPICS.get(category) or CATEGORY_TOPICS["other"]


def fundamentals_for(target_role: str) -> list[tuple[str, str, list[str]]]:
    import re
    role = target_role.lower()
    for keywords, topics in ROLE_FUNDAMENTALS:
        if any(re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", role) for k in keywords):
            return topics
    return DEFAULT_FUNDAMENTALS
