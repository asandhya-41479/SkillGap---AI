"""Adds the 3 Module 7 lines to app/main.py (safe to run twice: it skips lines that are already there).
Run from the backend folder:  python -m scripts.patch_main_for_career
"""
from pathlib import Path

MAIN = Path("app/main.py")
EDITS = [  # (anchor line already in main.py, line to add after it)
    ("from app.models import job", "from app.models import career  # noqa: F401  (Module 7 tables)"),
    ("from app.api.routes import readiness as readiness_routes", "from app.api.routes import career as career_routes"),
    ("app.include_router(readiness_routes.router)", "app.include_router(career_routes.router)"),
]

text = MAIN.read_text(encoding="utf-8")
lines = text.splitlines()
for anchor, new in EDITS:
    if any(l.strip().startswith(new.split("  #")[0].strip()) for l in lines):
        print(f"already present: {new}")
        continue
    idx = next((i for i, l in enumerate(lines) if l.strip().startswith(anchor)), None)
    if idx is None:
        raise SystemExit(f"Could not find '{anchor}' in app/main.py. Add this line manually: {new}")
    lines.insert(idx + 1, new)
    print(f"added: {new}")
MAIN.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("app/main.py updated.")
