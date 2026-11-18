"""Prints similarity scores for known pairs so you can confirm the ONNX model behaves like before.

Run from backend/:   python scripts/check_embeddings.py
Expected pattern (thresholds: strong >= 0.80, partial >= 0.45):
  very similar pairs (Python vs Python programming, React vs React.js)  -> high (about 0.8-1.0)
  related pairs (PostgreSQL vs SQL databases, Flask vs FastAPI)          -> middle
  unrelated pairs (Python vs Photoshop)                                  -> low
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.embedding_service import embedding_service  # noqa: E402

PAIRS = [
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
    for a, b in PAIRS:
        print(f"{a:40} vs {b:45} -> {embedding_service.cosine_similarity(a, b):.4f}")
