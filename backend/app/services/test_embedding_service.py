from app.services.embedding_service import embedding_service

test_pairs = [
    ("Python (programming_language)", "Python programming (programming_language)"),
    ("React (framework)", "React.js (framework)"),
    ("PostgreSQL (database)", "SQL databases (database)"),
    ("Python (programming_language)", "FastAPI (framework)"),
    ("Flask (framework)", "FastAPI (framework)"),
    ("Java (programming_language)", "JavaScript (programming_language)"),
    ("Docker (devops)", "Kubernetes (devops)"),
    ("Python (programming_language)", "Photoshop (tool)"),
]

if __name__ == "__main__":
    for a, b in test_pairs:
        score = embedding_service.cosine_similarity(a, b)
        print(f"{a!r:45} vs {b!r:45} -> {score:.4f}")