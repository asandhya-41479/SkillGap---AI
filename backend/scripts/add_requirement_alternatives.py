"""Adds job_requirements.alternatives (Phase 1A). Safe to run more than once.

create_all() never adds a column to a table that already exists, so existing databases
(your laptop and Neon) need this once. New databases get the column from the model.

Run from backend/:   python scripts/add_requirement_alternatives.py
On Neon you can instead paste the same SQL into the SQL Editor:
    ALTER TABLE job_requirements ADD COLUMN IF NOT EXISTS alternatives JSON;
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

import app.main  # noqa: E402,F401  (registers every model, same as repair_roadmaps.py)
from app.db.database import engine  # noqa: E402

SQL = "ALTER TABLE job_requirements ADD COLUMN IF NOT EXISTS alternatives JSON"

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.execute(text(SQL))
    print("OK: job_requirements.alternatives is present.")
